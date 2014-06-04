'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('dareyoo.services', []).
    factory('dareyooAPI', function() {
      var shinyNewServiceInstance;
      //factory function body that constructs shinyNewServiceInstance
      return shinyNewServiceInstance;
    }).
    factory('blob', function() {
        //http://stackoverflow.com/questions/18550151/posting-base64-data-javascript-jquery
        //http://pastebin.com/1E2FAM5K
        return function dataURLToBlob(dataURL) {
          var BASE64_MARKER = ';base64,';
          if (dataURL.indexOf(BASE64_MARKER) == -1) {
            var parts = dataURL.split(',');
            var contentType = parts[0].split(':')[1];
            var raw = parts[1];
            return new Blob([raw], {type: contentType});
          } else {
            var parts = dataURL.split(BASE64_MARKER);
            var contentType = parts[0].split(':')[1];
            var raw = window.atob(parts[1]);
            var rawLength = raw.length;
     
            var uInt8Array = new Uint8Array(rawLength);
     
            for (var i = 0; i < rawLength; ++i) {
             uInt8Array[i] = raw.charCodeAt(i);
           }
     
           return new Blob([uInt8Array], {type: contentType});
         }
       };
    });