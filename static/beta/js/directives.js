
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
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-pic.html',
      link: function(scope, element, attrs) {
        var size = 'small';
        if(['micro', 'small', 'big'].indexOf(attrs.size) != -1) size = attrs.size;
        if(size == 'micro') { scope.img_width = scope.img_height = 40; }
        if(size == 'small') { scope.img_width = scope.img_height = 50; }
        if(size == 'big') { scope.img_width = scope.img_height = 60; }
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
}]);