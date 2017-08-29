const config = {
    color: '#225159'
};

class Script {
    /**
     * @params {object} request
     */
    prepare_outgoing_request({ request }) {
        const trigger = request.data.trigger_word.toLowerCase() + ' ';
        const phrase = request.data.text.toLowerCase().replace(trigger, '').replace(/ /g, '+');
        let u = '';
        let data = {};
        let m = 'GET';
        if(trigger.indexOf('tc register') !== -1) {
                u = request.url;
                  data = {
                  'name': request.data.user_id,
                  'username': request.data.user_name
                };
                m = 'POST';
                  
        }
          else if(trigger.indexOf('tc complete') !== -1) {
                m = 'PUT';
                u = request.url + "complete/" + request.data.user_id;
            } 
          else if(trigger.indexOf('tc shame') !== -1) {
                u = request.url + "shame";
             
           
        } else if(trigger.indexOf('tc stop') !== -1) {
                u = request.url + request.data.user_id;
                  m = 'DELETE'
             
           
        } else if(trigger.indexOf('tc help') !== -1) {
                u = request.url + "help";
             
           
        } else {
            
            return {
              text: "This is the time card rocket chat tool.\nTest\nTest"
            }
            
       }
        return {
            url: u,
              headers: {'content-type':'application/json'},
            method: m,
            data: data
            
        };
    }

    process_outgoing_response({ request, response }) {
            return {
                content: {
                    text:  response.content.out
                }
            };
        
    }

}

      function showProps(obj, objName) {
          var result = '';
          for (var i in obj) {
            // obj.hasOwnProperty() is used to filter out properties from the object's prototype chain
            if (obj.hasOwnProperty(i)) {
                  result += objName + '.' + i + ' = ' + obj[i] + '\n';
            }
          }
      return result;
    }
