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
  'dareyoo.directives'
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
config(['$stateProvider', '$urlRouterProvider', '$locationProvider', 'config', function($stateProvider, $urlRouterProvider, $locationProvider, config) {
    $urlRouterProvider.otherwise("/main/timeline");
    $locationProvider.html5Mode(true).hashPrefix('!'); // enable pushState
    $stateProvider
        .state('main', {
          url: "/main",
          //templateUrl: "/static/alpha/partials/main.html",
          templateUrl: config.static_url + "beta/build/partials/main.html",
          controller: 'MainCtrl'
        })
        .state('main.bet', {
          url: "/bet/:betId",
          //templateUrl: "/static/alpha/partials/bet.html",
          templateUrl: config.static_url + "beta/build/partials/bet.html",
          controller: 'BetCtrl'
        })
        .state('main.new-bet', {
          url: "/new-bet",
          //templateUrl: "/static/alpha/partials/new-bet.html",
          templateUrl: config.static_url + "beta/build/partials/new-bet.html",
          controller: 'NewBetCtrl'
        })
        .state('main.new-bet-simple', {
          url: "/new-bet-simple",
          //templateUrl: "/static/alpha/partials/new-bet-simple.html",
          templateUrl: config.static_url + "beta/build/partials/new-bet-simple.html",
          controller: 'NewBetCtrl'
        })
        .state('main.new-bet-auction', {
          url: "/new-bet-auction",
          //templateUrl: "/static/alpha/partials/new-bet-auction.html",
          templateUrl: config.static_url + "beta/build/partials/new-bet-auction.html",
          controller: 'NewBetCtrl'
        })
        .state('main.new-bet-lottery', {
          url: "/new-bet-lottery",
          //templateUrl: "/static/alpha/partials/new-bet-lottery.html",
          templateUrl: config.static_url + "beta/build/partials/new-bet-lottery.html",
          controller: 'NewBetCtrl'
        })
        .state('main.timeline', {
          url: "/timeline",
          //templateUrl: "/static/alpha/partials/timeline.html",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineCtrl'
        })
        .state('main.timeline-global', {
          url: "/timeline-global",
          //templateUrl: "/static/alpha/partials/timeline.html",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineGlobalCtrl'
        })
        .state('main.timeline-conflicts', {
          url: "/timeline-conflicts",
          //templateUrl: "/static/alpha/partials/timeline.html",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineConflictsCtrl'
        })
        .state('main.timeline-search', {
          url: "/timeline-search",
          //templateUrl: "/static/alpha/partials/timeline.html",
          templateUrl: config.static_url + "beta/build/partials/timeline.html",
          controller: 'TimelineSearchCtrl'
        })
        .state('main.open-bets', {
          url: "/open-bets",
          //templateUrl: "/static/alpha/partials/timeline-by-state.html",
          templateUrl: config.static_url + "beta/build/partials/timeline-by-state.html",
          controller: 'OpenBetsCtrl'
        })
        .state('profile', {
          url: "/profile/:userId",
          //templateUrl: "/static/alpha/partials/profile.html",
          templateUrl: config.static_url + "beta/build/partials/profile.html",
          controller: 'UserCtrl'
        })
        .state('profile.following', {
          url: "/following",
          //templateUrl: "/static/alpha/partials/profile_following.html",
          templateUrl: config.static_url + "beta/build/partials/profile_following.html",
          controller: 'ProfileFollowingCtrl'
        })
        .state('profile.followers', {
          url: "/followers",
          //templateUrl: "/static/alpha/partials/profile_followers.html",
          templateUrl: config.static_url + "beta/build/partials/profile_followers.html",
          controller: 'ProfileFollowersCtrl'
        })
        .state('profile.bets', {
          url: "/bets",
          //templateUrl: "/static/alpha/partials/profile_bets.html",
          templateUrl: config.static_url + "beta/build/partials/profile_bets.html",
          controller: 'ProfileBetsCtrl'
        })
        .state('rankings', {
          url: "/rankings",
          //templateUrl: "/static/alpha/partials/rankings.html",
          templateUrl: config.static_url + "beta/build/partials/rankings.html",
          controller: 'RankingCtrl'
        })
}]).
run(['$http', '$cookies', '$rootScope', '$state', '$stateParams', '$timeout', function run($http, $cookies, $rootScope, $state, $stateParams, $timeout) {
    // For CSRF token compatibility with Django
    $http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];

    // It's very handy to add references to $state and $stateParams to the $rootScope
    // so that you can access them from any scope within your applications.For example,
    // <li ng-class="{ active: $state.includes('contacts.list') }"> will set the <li>
    // to active whenever 'contacts.list' or one of its decendents is active.
    $rootScope.$state = $state;
    $rootScope.$stateParams = $stateParams;
    $rootScope.user = null;
    $rootScope.new_notifications = 0;
    $rootScope.notifications = [];
    $rootScope.q = {'query': ""};

    $rootScope.getMe = function() {
      $http.get("/api/v1/me/").success(function(response) {
          $rootScope.user = response;
      });
      $timeout($rootScope.getMe, 5000);
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
    $rootScope.getNotifications();
}]).
constant('moment', moment).
constant('config', {static_url:'/static/'});