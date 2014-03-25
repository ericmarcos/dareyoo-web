
'use strict';

/* Directives */


angular.module('dareyoo.directives', [])
  .directive('dyBetListItem', function() {
    return {
      restrict: 'E',
      scope: {
        bet: '='
      },
      //templateUrl: '/static/alpha/partials/directives/dy-bet-list-item.html'
      templateUrl: '//s3-eu-west-1.amazonaws.com/dareyoo/alpha/partials/directives/dy-bet-list-item.html'
    };
  })
  .directive('dyUserPic', function() {
    return {
      restrict: 'E',
      scope: {
        user: '=',
      },
      //templateUrl: '/static/alpha/partials/directives/dy-user-pic.html',
      templateUrl: '//s3-eu-west-1.amazonaws.com/dareyoo/alpha/partials/directives/dy-user-pic.html',
      link: function(scope, element, attrs) {
        var size = 'small';
        if(['micro', 'small', 'big'].indexOf(attrs.size) != -1) size = attrs.size;
        if(size == 'micro') { scope.img_width = scope.img_height = 40; }
        if(size == 'small') { scope.img_width = scope.img_height = 50; }
        if(size == 'big') { scope.img_width = scope.img_height = 60; }
      }
    };
  })
  .directive('dyUserName', function() {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        inAlert: '='
      },
      //templateUrl: '/static/alpha/partials/directives/dy-user-name.html'
      templateUrl: '//s3-eu-west-1.amazonaws.com/dareyoo/alpha/partials/directives/dy-user-name.html'
    };
  })
  .directive('dyBiddingDeadline', function() {
    return {
      restrict: 'E',
      scope: {
        limit: '='
      },
      //templateUrl: '/static/alpha/partials/directives/dy-bidding-deadline.html'
      templateUrl: '//s3-eu-west-1.amazonaws.com/dareyoo/alpha/partials/directives/dy-bidding-deadline.html'
    };
  })
  .directive('dyEventDeadline', function() {
    return {
      restrict: 'E',
      scope: {
        limit: '='
      },
      //templateUrl: '/static/alpha/partials/directives/dy-event-deadline.html'
      templateUrl: '//s3-eu-west-1.amazonaws.com/dareyoo/alpha/partials/directives/dy-event-deadline.html'
    };
  });