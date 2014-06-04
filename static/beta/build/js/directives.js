
'use strict';

/* Directives */


angular.module('dareyoo.directives', [])
  .directive('dyBetListItem', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        bet: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-bet-list-item.html'
    };
  }])
  .directive('dyUserPic', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        size: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-pic.html',
      link: function(scope, element, attrs) {
        var size = 'small';
        if(['micro', 'small', 'big', 'xl'].indexOf(scope.size) != -1) size = scope.size;
        if(size == 'micro') { scope.img_width = scope.img_height = 40; }
        if(size == 'small') { scope.img_width = scope.img_height = 50; }
        if(size == 'big') { scope.img_width = scope.img_height = 60; }
        if(size == 'xl') { scope.img_width = scope.img_height = 80; }
        scope.$watch('size', function(newValue, oldValue) {
          if (newValue) {
            if(['micro', 'small', 'big', 'xl'].indexOf(newValue) != -1) size = newValue;
            if(size == 'micro') { scope.img_width = scope.img_height = 40; }
            if(size == 'small') { scope.img_width = scope.img_height = 50; }
            if(size == 'big') { scope.img_width = scope.img_height = 60; }
            if(size == 'xl') { scope.img_width = scope.img_height = 80; }
          }
        }, true);
      }
    };
  }])
  .directive('dyUserName', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        inAlert: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-name.html'
    };
  }])
  .directive('dyUserPicName', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        inAlert: '=',
        size: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-pic-name.html',
      link: function(scope, element, attrs) {
        scope.size = attrs.size;
      }
    };
  }])
  .directive('dyBiddingDeadline', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        limit: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-bidding-deadline.html'
    };
  }])
  .directive('dyEventDeadline', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        limit: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-event-deadline.html'
    };
  }])
  .directive("fileread", [function () {
    //http://stackoverflow.com/questions/17063000/ng-model-for-input-type-file
    return {
        link: function (scope, element, attributes) {
            element.bind("change", function (changeEvent) {
                var reader = new FileReader();
                reader.onload = function (loadEvent) {
                    scope.$apply(function () {
                        scope.fileread = loadEvent.target.result;
                    });
                }
                reader.readAsDataURL(changeEvent.target.files[0]);
            });
        }
    }
  }])
  .directive('dyNewBetWidget', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        limit: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-new-bet-widget.html'
    };
  }])
  .directive('dyLoader', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        limit: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-loader.html'
    };
  }]);