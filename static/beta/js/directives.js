
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
  .directive('dyExperienceLevelBar', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        experience: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-experience-level-bar.html',
      controller: ["$scope", "$element", "$attrs", "$transclude", "config", function($scope, $element, $attrs, $transclude, config) {
        $scope.levelPercent = function() {
          if($scope.experience) {
            var user_points_current_level = $scope.experience.points - $scope.experience.prev_level;
            var points_current_level = $scope.experience.next_level - $scope.experience.prev_level;
            var percent = user_points_current_level / points_current_level * 100;
            if(percent < 3) return 3;
            return percent;
          }
        };
      }]
    };
  }])
  .directive('dyLevelStar', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        level: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-level-star.html'
    };
  }])
  .directive('dyUserPic', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        size: '=',
        badges: '='
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-pic.html',
      link: function(scope, element, attrs) {
        var size = 'small';
        var s = scope.size || attrs.size;
        if(!angular.isDefined(scope.badges)) {
          scope.show_badges = true;
        }
        if(['micro', 'small', 'big', 'xl', 'xxl'].indexOf(s) != -1) size = s;
        if(size == 'micro') { scope.img_width = scope.img_height = 40; }
        if(size == 'small') { scope.img_width = scope.img_height = 50; }
        if(size == 'big') { scope.img_width = scope.img_height = 60; }
        if(size == 'xl') { scope.img_width = scope.img_height = 80; }
        if(size == 'xxl') { scope.img_width = scope.img_height = 100; }
        scope.$watch('size', function(newValue, oldValue) {
          if (newValue) {
            if(['micro', 'small', 'big', 'xl', 'xxl'].indexOf(newValue) != -1) size = newValue;
            if(size == 'micro') { scope.img_width = scope.img_height = 40; }
            if(size == 'small') { scope.img_width = scope.img_height = 50; }
            if(size == 'big') { scope.img_width = scope.img_height = 60; }
            if(size == 'xl') { scope.img_width = scope.img_height = 80; }
            if(size == 'xxl') { scope.img_width = scope.img_height = 100; }
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
        inAlert: '=',
        inverted: '=',
        big: '=',
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-name.html'
    };
  }])
  .directive('dyUserSummary', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        user: '=',
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-summary.html',
      controller: ["$scope", "$element", "$attrs", "$transclude", "config", function($scope, $element, $attrs, $transclude, config) {
        $scope.getBadgePath = function(badge, level) {
          return config.static_url + "beta/build/img/app/badges/" + badge + ".png";
        };
      }]
    };
  }])
  .directive('dyUserPicName', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        inAlert: '=',
        size: '=',
        horizontal: '=',
        badges: '=',
        big: '=',
        inverted: '=',
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-pic-name.html',
    };
  }])
  .directive('dyUserList', ['config', function(config) {
    return {
      restrict: 'E',
      scope: {
        users: '=',
        loggedInId: '=',
      },
      templateUrl: config.static_url + 'beta/build/partials/directives/dy-user-list.html',
      controller: ["$scope", "$element", "$attrs", "$transclude", "$http", "config", function($scope, $element, $attrs, $transclude, $http, config) {
        $scope.followUser = function(user) {
          $http.post(document.location.origin + "/api/v1/users/" + user.id + "/follow/").success(function(response) {
            $scope.$broadcast('follow_unfollow');
            user.im_following = true;
          });
        };
        $scope.unfollowUser = function(user) {
          $http.post(document.location.origin + "/api/v1/users/" + user.id + "/unfollow/").success(function(response) {
            $scope.$broadcast('follow_unfollow');
            user.im_following = false;
          });
        };
      }]
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