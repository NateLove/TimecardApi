from flask import Flask
from flask_restplus import Api, Resource, fields
from pymongo import MongoClient
import time
from datetime import datetime, timedelta


client = MongoClient()
db = client.test

app = Flask(__name__)
api = Api(app, version='1.0', title='CS Consulting Timecard API',
    description='API to manage time cards for the CS consulting team',doc='/swagger-secret/'
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

    def add_completion(self, complete=True, date=None):
        updated = False
        if date is None:
            date = Timecard.get_card_date()
        for card in self.timecards:
            if card['date'] == date:
                card['complete'] = complete
                updated = True
        if not updated:
            self.timecards.append({'date': date, 'complete': complete})
    @staticmethod
    def get_card_date():
        if datetime.now().weekday() == 4:
            return datetime.now().strftime("%x")
        if datetime.now().weekday() in [1,2,3]:
            days_ahead = 4 - datetime.now().weekday()
            next_friday = datetime.now() + timedelta(days_ahead)
            return next_friday.strftime("%x")
        if datetime.now().weekday() in [5,6,0]:
            days_behind = datetime.now().weekday() - 4
            if days_behind == -4:
                days_behind = 3
            prev_friday = datetime.now() - timedelta(days_behind)
            return prev_friday.strftime("%x")




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
            return {'out':'User not found. You may need to register. For more info try /tc help'}

    def update(self, id, name):
        try:
            self.db.update_one({'name': id}, {"$set": {'username':name}})
            return {'out': "User @{} updated".format(name)}
        except IndexError:
            return {'out':'User not found. You may need to register. For more info try /tc help'}

    def delete(self, name):
        self.db.delete_many({'name':name})
        return {'out':'User removed from list'}

    def complete(self, name, complete=True):
        if datetime.today().weekday() not in [5,6,4,0]:
            return {'out': 'Timecards can only be completed Friday-Monday'}
        try:
            t = Timecard(self.db, list(self.db.find({'name': name}))[0])
            t.add_completion(complete=complete)
            t.write_to_db()
            return {'out': "User: @{} marked timecard as complete".format(t.username)}
        except IndexError:
            return {'out':'User not found. You may need to register. For more info try /tc help'}

    def get_complete(self, name):
        try:
            t = Timecard(self.db, list(self.db.find({'name': name}))[0])
            return {'completed_timecards': t.timecards}
        except IndexError:
            return {'out':'User not found. You may need to register. For more info try /tc help'}
    def shame(self, id, name):
        if id != 'rocket.cat' :
            return {'out': "Only bots are allowed to shame. Shame on you @{}".format(name)}
        ulist = []
        now = datetime.now()
        for doc in self.db.find():
            tcs = doc.get('timecards', [])
            if tcs == []:
                ulist.append('@' + doc.get('username'))
            else:
                last_complete = datetime.strptime(tcs[-1]['date'], '%x')
                if last_complete.strftime("%x") != Timecard.get_card_date():
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


@ns.route('/<string:id>/<string:name>')
@ns.response(404, 'Person not found')
class Person(Resource):
    '''Show a single person and lets you delete them'''
    @ns.doc('get_person')
    @ns.marshal_with(timecard)
    def get(self, id, name):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_person')
    @ns.response(204, 'person deleted')
    def delete(self, id):
        '''Delete a person given its identifier'''
        return DAO.delete(id)


    def put(self, id, name):
        '''Update a person given its identifier'''
        return DAO.update(id, name)

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
@ns.route('/shame/<string:id>/<string:name>')
class Test(Resource):
  def get(self, id, name):
    return DAO.shame(id, name)
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
        return { 'out': 'This is the timecard rocketchat tool\n\nUsage:\n    /tc help - show this message\n    /tc register - add your username to the service\n    /tc complete - mark time card as complete\n    /tc update - update name info incase you change your displayed username\n    /tc stop - remove your username from the service'}
if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='/var/log/timecard.log',level=logging.DEBUG)
    app.run(debug=True,host='0.0.0.0')
