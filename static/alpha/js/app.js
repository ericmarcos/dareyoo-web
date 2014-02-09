'use strict';


// Declare app level module which depends on filters, and services
var dareyooApp = angular.module('dareyoo', [
  'ngCookies',
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
config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise("/main/timeline");
    $stateProvider
        .state('main', {
          url: "/main",
          templateUrl: "/static/alpha/partials/main.html",
          controller: 'MainCtrl'
        })
        .state('main.bet', {
          url: "/bet/:betId",
          templateUrl: "/static/alpha/partials/bet.html",
          controller: 'BetCtrl'
        })
        .state('main.new-bet', {
          url: "/new-bet",
          templateUrl: "/static/alpha/partials/new-bet.html",
          controller: 'NewBetCtrl'
        })
        .state('main.new-bet-simple', {
          url: "/new-bet-simple",
          templateUrl: "/static/alpha/partials/new-bet-simple.html",
          controller: 'NewBetCtrl'
        })
        .state('main.new-bet-auction', {
          url: "/new-bet-auction",
          templateUrl: "/static/alpha/partials/new-bet-auction.html",
          controller: 'NewBetCtrl'
        })
        .state('main.new-bet-lottery', {
          url: "/new-bet-lottery",
          templateUrl: "/static/alpha/partials/new-bet-lottery.html",
          controller: 'NewBetCtrl'
        })
        .state('main.timeline', {
          url: "/timeline",
          templateUrl: "/static/alpha/partials/timeline.html",
          controller: 'TimelineCtrl'
        })
        .state('main.timeline-global', {
          url: "/timeline-global",
          templateUrl: "/static/alpha/partials/timeline.html",
          controller: 'TimelineGlobalCtrl'
        })
        .state('main.timeline-conflicts', {
          url: "/timeline-conflicts",
          templateUrl: "/static/alpha/partials/timeline.html",
          controller: 'TimelineConflictsCtrl'
        })
        .state('main.timeline-search', {
          url: "/timeline-search",
          templateUrl: "/static/alpha/partials/timeline.html",
          controller: 'TimelineSearchCtrl'
        })
        .state('main.open-bets', {
          url: "/open-bets",
          templateUrl: "/static/alpha/partials/timeline-by-state.html",
          controller: 'OpenBetsCtrl'
        })
        .state('profile', {
          url: "/profile/:userId",
          templateUrl: "/static/alpha/partials/profile.html",
          controller: 'UserCtrl'
        })
        .state('profile.following', {
          url: "/following",
          templateUrl: "/static/alpha/partials/profile_following.html",
          controller: 'ProfileFollowingCtrl'
        })
        .state('profile.followers', {
          url: "/followers",
          templateUrl: "/static/alpha/partials/profile_followers.html",
          controller: 'ProfileFollowersCtrl'
        })
        .state('profile.bets', {
          url: "/bets",
          templateUrl: "/static/alpha/partials/profile_bets.html",
          controller: 'ProfileBetsCtrl'
        })
        .state('rankings', {
          url: "/rankings",
          templateUrl: "/static/alpha/partials/rankings.html",
          controller: 'RankingCtrl'
        })
}]).
run(['$http', '$cookies', '$rootScope', '$state', '$stateParams', function run($http, $cookies, $rootScope, $state, $stateParams) {
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

    $http.get("/api/v1/me/").success(function(response) {
        $rootScope.user = response;
        $rootScope.new_notifications = 3;
        $rootScope.notifications = [1, 2, 3];
    });
}]).
constant('moment', moment);