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
      	
        if(trigger.indexOf('karmabot') !== -1) {
                m = 'POST';
            	data =  request.data;
            	u = request.url;
                if(request.data.text.indexOf("karmabot's") !== -1) {
					return {};
                }
            	if(request.data.text.indexOf('karmabot list') !== -1) {
        			u = request.url + 'list/' + request.data.user_name;
                }
        	
        } else {
          
            if (request.data.text.length > 50)
              return { };
            if (request.data.text.indexOf(' ') !== -1)
              return { };
            
            if(request.data.text.indexOf('++') !== -1) {
           		m = 'POST';
            	data =  request.data;
            	u = request.url + request.data.user_name;
                if(request.data.text.indexOf("karmabot's") !== -1) {
					return {};
                }
    		}
          	if(request.data.text.indexOf('--') !== -1) {
           		m = 'POST';
                data =  request.data;
            	u = request.url + request.data.user_name;
                if(request.data.text.indexOf("karmabot's") !== -1) {
					return {};
                }
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
      		if(response.status_code == 400) {
              return { }
            }
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
