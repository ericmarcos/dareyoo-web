'use strict';


// Declare app level module which depends on filters, and services
var dareyooApp = angular.module('dareyoo', [
  'ngCookies',
  'ngRoute',
  'ui.router',
  'ui.bootstrap',
  'timeRelative',
  'dareyoo.services',
  'dareyoo.controllers',
  'dareyoo.directives',
  'dareyoo.filters'
]).
config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('[[');
  $interpolateProvider.endSymbol(']]');
}]).
config(['$sceDelegateProvider', function($sceDelegateProvider) {
  $sceDelegateProvider.resourceUrlWhitelist([
    // Allow same origin resource loads.
    'self',
    // Allow loading from outer templates domain.
    'http://s3-eu-west-1.amazonaws.com/dareyoo/**'
  ]); 
}]).
/*config(['FacebookProvider', 'config', function(FacebookProvider, config) {
     FacebookProvider.init(config.fb_key);
}]).*/
config(['$stateProvider', '$urlRouterProvider', '$locationProvider', 'config', function($stateProvider, $urlRouterProvider, $locationProvider, config) {
    $urlRouterProvider.otherwise("/main/timeline-global");
    $locationProvider.html5Mode(true).hashPrefix('!'); // enable pushState
    $stateProvider
        .state('main', {
          url: "/main",
          templateUrl: config.static_url + "beta/build/partials/main.html",
          controller: 'MainCtrl'
        })
        .state('main.bet', {
          url: "/bet/:betId",
          templateUrl: config.static_url + "beta/build/partials/bet.html",
          controller: 'BetCtrl'
        })
        .state('main.timeline', {
          url: "/timeline",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineCtrl'
        })
        .state('main.timeline-global', {
          url: "/timeline-global",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineGlobalCtrl'
        })
        .state('main.timeline-conflicts', {
          url: "/timeline-conflicts",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineConflictsCtrl'
        })
        .state('main.timeline-search', {
          url: "/timeline-search",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineSearchCtrl'
        })
        .state('main.open-bets', {
          url: "/open-bets",
          templateUrl: config.static_url + "beta/build/partials/timeline-by-state.html",
          controller: 'OpenBetsCtrl'
        })
        .state('profile', {
          url: "/profile/:userId",
          templateUrl: config.static_url + "beta/build/partials/profile.html",
          controller: 'UserCtrl'
        })
        .state('profile.following', {
          url: "/following",
          templateUrl: config.static_url + "beta/build/partials/profile_following.html",
          controller: 'ProfileFollowingCtrl'
        })
        .state('profile.followers', {
          url: "/followers",
          templateUrl: config.static_url + "beta/build/partials/profile_followers.html",
          controller: 'ProfileFollowersCtrl'
        })
        .state('profile.bets', {
          url: "/bets",
          templateUrl: config.static_url + "beta/build/partials/profile_bets.html",
          controller: 'ProfileBetsCtrl'
        })
        .state('rankings', {
          url: "/rankings",
          templateUrl: config.static_url + "beta/build/partials/rankings.html",
          controller: 'RankingCtrl'
        })
        .state('tournaments', {
          url: "/tournaments",
          templateUrl: config.static_url + "beta/build/partials/tournaments.html",
          controller: 'TournamentsCtrl'
        })
        .state('tournament-detail', {
          url: "/tournament/:tournamentId",
          templateUrl: config.static_url + "beta/build/partials/tournament-detail.html",
          controller: 'TournamentCtrl'
        })
        .state('edit-profile', {
          url: "/edit-profile",
          templateUrl: config.static_url + "beta/build/partials/edit-profile.html",
          controller: 'EditProfileCtrl'
        })
        .state('who-to-follow', {
          url: "/who-to-follow",
          templateUrl: config.static_url + "beta/build/partials/who-to-follow.html",
          controller: 'WhoToFollowCtrl'
        })
}]).
run(['$http', '$cookies', '$rootScope', '$state', '$stateParams', '$timeout', 'config', function run($http, $cookies, $rootScope, $state, $stateParams, $timeout, config) {
    // For CSRF token compatibility with Django
    $http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
    $http.defaults.headers.put['X-CSRFToken'] = $cookies['csrftoken'];

    // It's very handy to add references to $state and $stateParams to the $rootScope
    // so that you can access them from any scope within your applications.For example,
    // <li ng-class="{ active: $state.includes('contacts.list') }"> will set the <li>
    // to active whenever 'contacts.list' or one of its decendents is active.
    $rootScope.$state = $state;
    $rootScope.$stateParams = $stateParams;
    $rootScope.user = null;
    $rootScope.followers = [];
    $rootScope.followers_names = {};
    $rootScope.new_notifications = 0;
    $rootScope.notifications = [];
    $rootScope.q = {'query': ""};

    $rootScope.getMe = function() {
      $http.get("/api/v1/me/").success(function(response) {
          $rootScope.user = response;
      });
      $timeout($rootScope.getMe, 5000);
    };
    $rootScope.getMyFollowers = function() {
      $http.get("/api/v1/me/followers").success(function(response) {
        if(response && response.length > 0) {
          $rootScope.followers = response;
          for (var i = $rootScope.followers.length - 1; i >= 0; i--) {
            $rootScope.followers_names[$rootScope.followers[i].username] = '';
          };
        }
      });
    };

    $rootScope.getNotifications = function() {
      $http.get("/api/v1/notifications/").success(function(response) {
        var not = [];
        if(response.results) not = response.results;
        else not = response;
        if(not.length > 0) {
          $rootScope.notifications = not;
          $rootScope.new_notifications = not.filter(function(elem) {return elem && elem.is_new;}).length;
        }
      });
      $timeout($rootScope.getNotifications, 5000);
    };

    $rootScope.notificationsClick = function() {
      $rootScope.new_notifications = 0;
      for (var i = $rootScope.notifications.length - 1; i >= 0; i--)
        $rootScope.notificationViewed($rootScope.notifications[i]);
    };

    $rootScope.notificationViewed = function(note) {
      if(note.is_new) {
        note.is_new = false;
        $http.post('/api/v1/notifications/' + note.id + '/mark_as_viewed/');
      }
    };

    $rootScope.notificationClick = function(note) {
      if(!note.readed) {
        note.readed = true;
        $http.post('/api/v1/notifications/' + note.id + '/mark_as_readed/');
      }
    }

    $rootScope.getMe();
    $rootScope.getMyFollowers();
    //$rootScope.getNotifications();

}]).
constant('moment', moment);