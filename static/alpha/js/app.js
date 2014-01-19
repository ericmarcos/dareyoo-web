'use strict';


// Declare app level module which depends on filters, and services
var dareyooApp = angular.module('dareyoo', [
  'ngCookies',
  'ui.router',
  'timeRelative',
  'dareyoo.services',
  'dareyoo.controllers'
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
        .state('main.new-bet', {
          url: "/new-bet",
          templateUrl: "/static/alpha/partials/new-bet.html",
          controller: 'NewBetCtrl'
        })
        .state('main.timeline', {
          url: "/timeline",
          templateUrl: "/static/alpha/partials/timeline.html",
          controller: 'TimelineCtrl'
        })
        .state('main.open-bets', {
          url: "/open-bets",
          templateUrl: "/static/alpha/partials/open-bets.html"
        })
        .state('profile', {
          url: "/profile",
          templateUrl: "/static/alpha/partials/profile.html"
        })
}]).
/*config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/timeline', {templateUrl: '/static/alpha/partials/timeline.html', controller: 'TimelineCtrl'});
  $routeProvider.when('/profile', {templateUrl: '/static/alpha/partials/profile.html', controller: 'ProfileCtrl'});
  $routeProvider.otherwise({redirectTo: '/timeline'});
}]).*/
run(['$http', '$cookies', function run($http, $cookies) {
    // For CSRF token compatibility with Django
    $http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
}]).
constant('moment', moment);