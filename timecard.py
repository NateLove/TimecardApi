from flask import Flask
from flask_restplus import Api, Resource, fields
from pymongo import MongoClient
import time
from datetime import datetime, timedelta


client = MongoClient()
db = client.test

app = Flask(__name__)
api = Api(app, version='1.0', title='CS Consulting Timecard API',
    description='API to manage time cards for the CS consulting team',doc='/swagger/'
)

ns = api.namespace('time', description='time operations')

timecard = api.model('time', {
    'name': fields.String(required=True, description='Real name of the person'),
    'username': fields.String(required=False, description='RC name of the person'),
    'timecards': fields.Raw(required=False, description='Timecard completion status', default=[])
})


class Timecard(object):
    def __init__(self, db, data):
        self.db = db
  	self.name = data.get('user_id') if 'user_id' in data else data.get('name')
  	self.username = data.get('user_name') if 'user_name' in data else data.get('username')
        self.timecards = data.get('timecards', [])

    def get_json(self):
        return { 'name': self.name,
                'username': self.username,
                'timecards': self.timecards}

    def write_to_db(self):
        self.db.update_one({'name': self.name, 'username': self.username}, {'$set': self.get_json()}, upsert=True)

    def add_completion(self, complete=True, date=time.strftime("%x")):
        updated = False
        for card in self.timecards:
            if card['date'] == date:
                card['complete'] = complete
                updated = True
        if not updated:
            self.timecards.append({'date': date, 'complete': complete})

class TimeDao(object):
    def __init__(self, db):
        self.db = db

    def list(self):
        ret = []
        for doc in self.db.find({},{'_id':0}):
            ret.append(doc)
        return ret

    def create(self, data):
        t = Timecard(self.db, data)
        people = list(self.db.find({'name':t.name, 'username':t.username}))
        if len(people) > 0:
            return {'out': "User: @{} already exists".format(t.username)}
        t.write_to_db()
        return {'out': "User: @{} has been registered".format(t.username)}

    def get(self, name):
        try:
            t = Timecard(self.db, list(self.db.find({'name': name}))[0])
            return t.get_json()
        except IndexError:
            api.abort(404, 'Name not found')

    def update(self, name, data):
        try:
            t_old = Timecard(self.db, list(self.db.find({'name': name}))[0])
            t_new = Timecard(self.db, data)
            t_new.timecards = t_old.timecards
            self.db.delete_one(t_old.get_json())
            t_new.write_to_db()
            return t_new.get_json()
        except IndexError:
            api.abort(404, 'Name not found')

    def delete(self, name):
        self.db.delete_many({'name':name})
        return {'out':'User removed from list'}

    def complete(self, name, complete=True):
        try:
            t = Timecard(self.db, list(self.db.find({'name': name}))[0])
            t.add_completion(complete=complete)
            t.write_to_db()
            return {'out': "User: @{} marked timecard as complete".format(t.username)}
        except IndexError:
            api.abort(404, {'out':'Name not found'})

    def get_complete(self, name):
        try:
            t = Timecard(self.db, list(self.db.find({'name': name}))[0])
            return {'completed_timecards': t.timecards}
        except IndexError:
            api.abort(404, 'Name not found')
    def shame(self):
        ulist = []
        now = datetime.now()
        for doc in self.db.find():
            tcs = doc.get('timecards', [])
            if tcs == []:
                ulist.append('@' + doc.get('username'))
            else:
                last_complete = datetime.strptime(tcs[-1]['date'], '%x')
                if last_complete < now-timedelta(days=4):
                    ulist.append('@' + doc.get('username'))

        if ulist == []:
            return {'out': 'No one to shame at this time'}
        else:
            return {'out': 'The following user(s) should be shamed: ' + ", ".join(ulist)}
    def clear(self):
        self.db.delete_many({})

DAO = TimeDao(db.time)


@ns.route('/')
class PersonList(Resource):
    '''Shows a list of all people, and lets you POST to add new people'''
    @ns.doc('list_people')
    def get(self):
        '''List all people'''
        return {'out': DAO.list()}

    @ns.expect(timecard)
    def post(self):
        '''Create a new person'''
        return DAO.create(api.payload), 201


@ns.route('/<string:id>')
@ns.response(404, 'Person not found')
class Person(Resource):
    '''Show a single person and lets you delete them'''
    @ns.doc('get_person')
    @ns.marshal_with(timecard)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_person')
    @ns.response(204, 'person deleted')
    def delete(self, id):
        '''Delete a person given its identifier'''
        return DAO.delete(id)


    @ns.expect(timecard)
    @ns.marshal_with(timecard)
    def put(self, id):
        '''Update a person given its identifier'''
        return DAO.update(id, api.payload)

@ns.route('/complete/<string:id>')
@ns.response(404, 'Person not found')
@ns.param('id', "The person identifier")
class TodoCompleted(Resource):
    '''View completed timecards and mark uncompleted timecards as complete'''
    @ns.doc('complete_timecards')
    def put(self,id):
        '''Mark task as complete'''
        return DAO.complete(id)

    '''Shows a list of all complete timecards'''
    @ns.doc('list_complete_timecards')
    def get(self,id):
        '''List all tasks'''
        return DAO.get_complete(id)
@ns.route('/shame')
class Test(Resource):
  def get(self):
    return DAO.shame()
@ns.route('/clear/<string:password>')
class Clear(Resource):
    def get(self, password):
        if password != 'asdfjkl;':
            return 'nopenopenope'

        else:
            DAO.clear()
@ns.route('/help')
class Help(Resource):
    def get(self):
        return { 'out': 'This is the timecard rocketchat tool\n\nUsage:\n    /tc help - show this message\n    /tc register - add your username to the service\n    /tc completed - mark time card as complete\n    /tc stop - remove your username from the service'}
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
