'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('dareyoo.services', []).
factory('dareyooAPI', function() {
  var shinyNewServiceInstance;
  //factory function body that constructs shinyNewServiceInstance
  return shinyNewServiceInstance;
});