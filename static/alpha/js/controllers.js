
'use strict';

/* Controllers */

angular.module('dareyoo.controllers', []).
  controller('TimelineCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.getTimeline = function() {
      $http.get("/api/v1/timeline").success(function(response) {
        $scope.bets = response.results;
        $scope.loaded = true;
      });
    }

    $scope.getTimeline();
  }])
  .controller('UserCtrl', [function() {

  }])
  .controller('NewBetCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.formData = {amount: 50,
                        title:'My first API bet!',
                        bidding_deadline: '2014-06-26T23:51:06+00:00',
                        description: 'This is a test Bet POST',
                        event_deadline: '2014-06-27T01:51:17+00:00',
                        'public': true};

    $scope.postNewBet = function() {
      $http.post("/api/v1/bets/", $scope.formData)
      .success(function(response, status, headers, config) {
        $scope.bets = response.results;
        $scope.loaded = true;
      })
      .error(function(response, status, headers, config) {
        alert(response);
      });
    };
  }])
  .controller('MainCtrl', [function() { //Notifications, logged user

  }]);
