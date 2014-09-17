
'use strict';

/* Controllers */

angular.module('dareyoo.controllers', []).
  controller('EditProfileCtrl', ['$scope', '$http', '$location', '$routeParams', 'config', 'blob', function($scope, $http, $location, $routeParams, config, blob) {
    $scope.new_user = $location.search()['new'];
    $scope.upload_state = 'initial';
    $scope.usernameError = '';
    
    $scope.userAPIError = function(response, status, headers, config) {
      $('#user-fail-message').text(JSON.stringify(response));
      $('#user-fail-modal').modal('show');
    };

    var initial_load = true;
    if($scope.user) {
      $scope.new_email = $scope.user.email;
      $scope.new_username = $scope.user.username;
      $scope.new_description = $scope.user.description;
      $scope.new_email_notifications = $scope.user.email_notifications;
      initial_load = false;
    } else {
      $scope.$watch('user', function() {
        if($scope.user && initial_load) {
          $scope.new_email = $scope.user.email;
          $scope.new_username = $scope.user.username;
          $scope.new_description = $scope.user.description;
          $scope.new_email_notifications = $scope.user.email_notifications;
          initial_load = false;
        }
      });
    }
    $scope.$watch('fileread', function() {
      if($scope.fileread) {
        //http://stackoverflow.com/questions/15328191/shrink-image-before-uploading-with-javascript
        $scope.upload_state = 'file_selected';
        var tmp_img = new Image();
        tmp_img.src = $scope.fileread;
        tmp_img.onload = function() {
          var canvas = document.createElement('canvas');
          canvas.width = 200;
          canvas.height = 200;
          var ctx = canvas.getContext('2d');
          var w = tmp_img.width;
          var h = tmp_img.height;
          if(w > h) {
            ctx.drawImage(tmp_img, (w - h) / 2, 0, h, h, 0, 0, 200, 200);
          } else {
            ctx.drawImage(tmp_img, 0, (h - w) / 2, w, w, 0, 0, 200, 200);
          }
          $scope.shrinked = canvas.toDataURL();
          $scope.new_pic = $scope.shrinked;
          $scope.upload_state = 'file_processed';
        }
      }
    });
    $scope.$watch('upload_state', function() {
      if($scope.upload_state == 'file_processed') {
        $('#new_pic_preview').animate({left:40, opacity:1});
        $('#old_pic_preview').animate({opacity:0.5});
      }
    });
    $scope.emptyUsername = function() {
      return $('#username').val().length == 0;
    }
    $scope.cancelFile = function() {
      $scope.upload_state = 'initial';
      $('#new_pic_preview').animate({left:0, opacity:0});
      $('#old_pic_preview').animate({opacity:1});
    }
    $scope.uploadFile = function(files) {
      $scope.upload_state = 'file_uploading';
      var fd = new FormData();
      var b = blob($scope.shrinked);
      fd.append("profile_pic", b, "profile_pic");
      $http.post($window.location.origin + "/api/v1/users/" + $scope.user.id + "/pic_upload/", fd, {
          withCredentials: true,
          headers: {'Content-Type': undefined},
          transformRequest: angular.identity
      }).success(function(){
        $scope.upload_state = 'initial';
        $scope.user.pic = $scope.user.pic + "?" + new Date().getTime(); //refreshing img
        $('#old_pic_preview').animate({opacity:1});
      }).error(function(){
        $scope.upload_state = 'file_uploaded_error';
        $('#old_pic_preview').animate({opacity:1});
      });
    };
    $scope.save = function() {
      if(!$scope.emptyUsername()) {
        var user_data = {
            email: $scope.new_email,
            username: $scope.new_username,
            description: $scope.new_description,
            email_notifications: $scope.new_email_notifications
        };
        var url = $window.location.origin + "/api/v1/users/" + $scope.user.id + "/";
        if($scope.new_user) {
          url += "?new=true";
        }
        $http.put(url, user_data).success(function(response){
          if($scope.new_user) {
            $scope.$state.go("who-to-follow");
          } else {
            $('#user-ok-modal').modal('show');
          }
        }).error($scope.userAPIError);
      } else {
        $scope.usernameError = 'Introduce un nombre de usuario válido';
      }
    };
  }]).
  controller('WhoToFollowCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.new_user = $location.search('new');
    $scope.provider = '';
    $scope.friends_list = [];
    $scope.search_friends = function(provider) {
      $scope.loaded = false;
      $scope.provider = provider;
      var url = $window.location.origin + "/api/v1/search-dareyoo-suggested/?description=true";
      if(provider == 'facebook')
        url = $window.location.origin + "/api/v1/search-facebook-friends/";
      $http.get(url).success(function(response) {
        if(response.results) $scope.friends_list = response.results;
        else $scope.friends_list = response;
        $scope.loaded = true;
      });
    };
    $scope.search_friends('dareyoo');
  }]).
  controller('RankingCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.ranking = [];
    $scope.getRanking = function(order) {
      $http.get($window.location.origin + "/api/v1/ranking/").success(function(response) {
        if(response.results) $scope.ranking = response.results;
        else $scope.ranking = response;
      });
    }

    $scope.getRanking();
  }]).
  controller('TournamentsCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.tournaments = [];
    $scope.getTournaments = function() {
      $http.get($window.location.origin + "/api/v1/tournaments/").success(function(response) {
        if(response.results) $scope.tournaments = response.results;
        else $scope.tournaments = response;
      });
    };
    $scope.getStartDate = function(t) {
      var t = moment(t.start).format('D/M/YYYY');
      return t;
    };
    $scope.getEndDate = function(t) {
      var t = moment(t.end).format('D/M/YYYY');
      return t;
    };

    $scope.getTournaments();
  }]).
  controller('TournamentCtrl', ['$scope', '$http', '$location', '$filter', '$stateParams', function($scope, $http, $location, $filter, $stateParams) {
    $scope.tournament = {};
    $scope.leaderboard = {};
    $scope.global = $stateParams.tournamentId == 0;
    $scope.loaded = false;
    $scope.getTournament = function(id) {
      $http.get($window.location.origin + "/api/v1/tournaments/" + id).success(function(response) {
        if(response.results) $scope.tournament = response.results;
        else $scope.tournament = response;
        $scope.loaded = true;
      });
    };
    $scope.getLeaderboard = function(id) {
      $http.get($window.location.origin + "/api/v1/tournaments/" + id + "/leaderboard").success(function(response) {
        if(response.results) $scope.leaderboard = response.results;
        else $scope.leaderboard = response;
        $scope.loaded = true;
      });
    };
    $scope.getStartDate = function() {
      if($scope.tournament.start) {
        var t = moment($scope.tournament.start).format('D/M/YYYY');
        return t;
      }
      return null
    };
    $scope.getEndDate = function() {
      if($scope.tournament.end) {
        var t = moment($scope.tournament.end).format('D/M/YYYY');
        return t;
      }
      return null;
    };
    if($scope.global) {
      $scope.getLeaderboard(0);
    } else {
      $scope.getTournament($stateParams.tournamentId);
      $scope.getLeaderboard($stateParams.tournamentId);
    }
  }]).
  controller('TimelineCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = null;
    $scope.order_by = "-created_at";
    $scope.loaded = false;
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get($window.location.origin + "/api/v1/timeline/", {'params': {'order': $scope.order_by}}).success(function(response) {
        if(response.results) {
          $scope.bets = response.results;
          $scope.more_bets_link = response.next;
        }
        else $scope.bets = response;
        $scope.loaded = true;
      });
    };
    $scope.moreBets = function() {
      $http.get($scope.more_bets_link).success(function(response) {
        if(response.results) {
          $scope.bets.push.apply($scope.bets, response.results);
          $scope.more_bets_link = response.next;
        }
      });
    };
    $scope.getTimeline();
  }]).
  controller('TimelineGlobalCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = null;
    $scope.order_by = "-created_at";
    $scope.loaded = false;
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get($window.location.origin + "/api/v1/timeline/", {'params': {'order': $scope.order_by, 'global': true}}).success(function(response) {
        if(response.results) {
          $scope.bets = response.results;
          $scope.more_bets_link = response.next;
        }
        else $scope.bets = response;
        $scope.loaded = true;
      });
    };
    $scope.moreBets = function() {
      $http.get($scope.more_bets_link).success(function(response) {
        if(response.results) {
          $scope.bets.push.apply($scope.bets, response.results);
          $scope.more_bets_link = response.next;
        }
      });
    };
    $scope.getTimeline();
  }]).
  controller('TimelineConflictsCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "complained_at";
    $scope.hide_order = true;
    $scope.loaded = false;
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get($window.location.origin + "/api/v1/timeline/", {'params': {'order': $scope.order_by, 'global': true, 'state': 'arbitrating'}}).success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    };

    $scope.getTimeline();
  }]).
  controller('SearchCtrl', ['$scope', '$rootScope', function($scope, $rootScope) {
    //$rootScope.q = "Euro";
    $scope.search = function() {
      $rootScope.$state.go("main.timeline-search", {}, {"reload": true});
    };
    $scope.onSearchEnter = function(event) {
      if (event && event.which && event.which == 13) {
        $rootScope.$state.go("main.timeline-search", {}, {"reload": true});
        //$rootScope.q.query = $('#search').val();
        //$('#search').val('');
      }
    };
  }]).
  controller('TimelineSearchCtrl', ['$scope', '$rootScope', '$http', '$location', '$filter', function($scope, $rootScope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";
    $scope.loaded = false;
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get($window.location.origin + "/api/v1/bets/search/", {'params': {'q': $rootScope.q.query}}).success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    };

    $scope.getTimeline();
  }]).
  controller('OpenBetsCtrl', ['$scope', '$rootScope', '$http', '$location', '$filter', function($scope, $rootScope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";
    $scope.loaded = false;

    $scope.getOpenBets = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get($window.location.origin + "/api/v1/me/open_bets/").success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    };

    $scope.getOpenBets();
  }])
  .controller('UserCtrl', ['$scope', '$rootScope', '$http', '$stateParams', 'config', function($scope, $rootScope, $http, $stateParams, config) {
    $scope.profile_user_follows_me = false;
    $scope.i_follow_profile_user = false;
    $scope.followers = [];
    $scope.following = [];
    $scope.loaded = false;

    $scope.getUser = function(id) {
      $http.get($window.location.origin + "/api/v1/users/" + id).success(function(response) {
        $scope.profile_user = response;
        $scope.$root.title = $scope.profile_user.username;
        $scope.loaded = true;
      });
    };
    /*$scope.getNBets = function(id, params, callback) {
      params = params || {};
      callback = callback || function(response) { $scope.n_bets = response.count; };
      $http.get($window.location.origin + "/api/v1/users/" + id + "/n_bets/", {'params': params}).success(callback);
    }*/
    $scope.followUser = function(id) {
      $http.post($window.location.origin + "/api/v1/users/" + id + "/follow/").success(function(response) {
        $scope.$broadcast('follow_unfollow');
      });
    };
    $scope.unfollowUser = function(id) {
      $http.post($window.location.origin + "/api/v1/users/" + id + "/unfollow/").success(function(response) {
        $scope.$broadcast('follow_unfollow');
        //$scope.loadUser();
      });
    };
    /*$scope.isFollowing = function(id, ask_id, success) {
      $http.get($window.location.origin + "/api/v1/users/" + id + "/is_following/", {'params': {'user_id': ask_id}}).success(success);
    };*/

    $scope.getBadgePath = function(badge, level) {
      return config.static_url + "beta/build/img/app/badges/" + badge + ".png";
    };
    $scope.loadUser = function() {
      var id = $stateParams.userId;
      $scope.getUser(id);
      //$scope.getNBets(id);
      /*if($rootScope.user) {
        $scope.isFollowing(id, $rootScope.user.id, function(response) {
          $scope.profile_user_follows_me = response.status;
        });
        $scope.isFollowing($rootScope.user.id, id, function(response) {
          $scope.i_follow_profile_user = response.status;
        });
      }*/
    };
    /*$rootScope.$watch('user', function() {
      $scope.loadUser();
    });*/
    $scope.$on('follow_unfollow', function(e) {  
      $scope.loadUser();
    });
    $scope.loadUser();

  }])
  .controller('ProfileFollowersCtrl', ['$scope', '$rootScope', '$http', '$stateParams', function($scope, $rootScope, $http, $stateParams) {
    $scope.getFollowers = function(id) {
      $http.get($window.location.origin + "/api/v1/users/" + id + "/followers/").success(function(response) {
        if(response.results) $scope.followers = response.results;
        else $scope.followers = response;
      });
    };
    $scope.$on('follow_unfollow', function(e) {  
      $scope.getFollowers($stateParams.userId);
    });
    $scope.getFollowers($stateParams.userId);
  }])
  .controller('ProfileFollowingCtrl', ['$scope', '$rootScope', '$http', '$stateParams', function($scope, $rootScope, $http, $stateParams) {
    $scope.getFollowing = function(id) {
      $http.get($window.location.origin + "/api/v1/users/" + id + "/following/").success(function(response) {
        if(response.results) $scope.following = response.results;
        else $scope.following = response;
      });
    };
    $scope.$on('follow_unfollow', function(e) {  
      $scope.getFollowing($stateParams.userId);
    });
    $scope.getFollowing($stateParams.userId);
  }])
  .controller('ProfileBetsCtrl', ['$scope', '$rootScope', '$http', '$stateParams', function($scope, $rootScope, $http, $stateParams) {
    $scope.getBets = function(id, params, callback) {
      params = params || {};
      callback = callback || function(response) { if(response.results) $scope.bets = response.results; else $scope.bets = response; };
      $http.get($window.location.origin + "/api/v1/users/" + id + "/bets/", {'params': params}).success(callback);
    };

    $scope.getBets($stateParams.userId, {'all':true});
  }])
  .controller('BetCtrl', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {
    $scope.bet = false;
    $scope.public_bet = true;
    $scope.loaded = false;
    $scope.bidTitle = "";
    $scope.bidAmount = 10;
    $scope.dialogs = {'bid': false, 'arbitrating':false};
    $scope.claims = {resolvingClaim: '', complainingClaim: '', arbitratingClaim: ''};
    $scope.current_bid_result = "";
    $scope.current_bid_participants = [];

    $scope.betWinner = function() {
      if($scope.bet.bet_type == 3) {
        if($scope.bet.referee_claim == 3)
          return null;
        return $scope.bet.referee_lottery_winner || $scope.bet.claim_lottery_winner;
      }
      return $scope.bet.referee_claim || $scope.bet.claim;
    };

    $scope.betAPIError = function(response, status, headers, config) {
      if(response && response['detail'] == "Authentication credentials were not provided.") {
        $scope.public_bet = true;
        $('#register-modal').modal('show');
      } else if(response && response['detail'] == "Not found" && !$scope.$root.user) {
        $scope.public_bet = false;
        $('#register-modal').modal('show');
      } else {
        $('#bet-fail-message').text(JSON.stringify(response));
        $('#bet-fail-modal').modal('show');
      }
    };

    $scope.getBet = function(id) {
      $http.get($window.location.origin + "/api/v1/bets/" + id).success(function(response) {
        $scope.bet = response;
        $scope.loaded = true;
        $scope.$root.title = $scope.bet.title;
        //$scope.bet.bet_state = "resolving";
        //$scope.bet.bet_type = 2;
        //$scope.bet.accepted_bid.author.id=2;
        //$scope.bet.points = 235;
        //$scope.bet.claim_lottery_winner = {'title': '0 - 2'};
      }).error($scope.betAPIError);
    };
    $scope.acceptBet = function() {
      $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/accept_bet/").success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.postBid = function(title, amount) {
      $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/bids/", {title: title, amount: amount}).success(function(response) {
        $scope.getBet($stateParams.betId);
        $scope.dialogs.bid = false;
        if($scope.user.id != $scope.bet.author.id && $scope.bet.bet_type == 3) {
          //Automatically participating in a result that you just created
          $scope.participateBid(response.id);
        }
      }).error($scope.betAPIError);
    };
    $scope.acceptBid = function(bidId) {
      $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/accept_bid/", {bid_id: bidId}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.participateBid = function(bidId) {
      $http.post($window.location.origin + "/api/v1/bids/" + bidId + "/add_participant/").success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.showParticipants = function(bid) {
      $http.get($window.location.origin + "/api/v1/bids/" + bid.id + "/participants/").success(function(response) {
        $scope.current_bid_result = bid.title;
        $scope.current_bid_participants = response;
        $('#bid-participants-modal').modal('show');
      }).error($scope.betAPIError);
      return false;
    };
    $scope.removeBid = function(bidId) {
      $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/remove_bid/", {bid_id: bidId}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.resolveBet = function(claim) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/resolve/", {claim: claim, claim_message: $scope.claims.resolvingClaim}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.resolveLottery = function(bidId, claim) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      if(claim == 3) {
        $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/resolve/", {claim: claim, claim_message: $scope.claims.resolvingClaim}).success(function(response) {
          $scope.getBet($stateParams.betId);
        }).error($scope.betAPIError);
      } else {
        $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/resolve/", {claim_lottery_winner: bidId, claim_message: $scope.claims.resolvingClaim}).success(function(response) {
          $scope.getBet($stateParams.betId);
        }).error($scope.betAPIError);
      }
    };
    $scope.complainBet = function(bid_id, claim) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      $http.post($window.location.origin + "/api/v1/bids/" + bid_id + "/complain/", {claim: claim, claim_message: $scope.claims.complainingClaim}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.complainLottery = function(claim_lottery_winner, claim) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      if(claim == 3) {
        $http.post($window.location.origin + "/api/v1/bids/" + claim_lottery_winner + "/complain/", {claim: claim, claim_message: $scope.claims.complainingClaim}).success(function(response) {
          $scope.getBet($stateParams.betId);
        }).error($scope.betAPIError);
      } else {
        $http.post($window.location.origin + "/api/v1/bids/" + claim_lottery_winner + "/complain/", {claim: 2, claim_message: $scope.claims.complainingClaim}).success(function(response) {
          $scope.getBet($stateParams.betId);
        }).error($scope.betAPIError);
      }
    };
    $scope.arbitrateBet = function(claim) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/arbitrate/", {claim: claim, claim_message: $scope.claims.arbitratingClaim}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.arbitrateLottery = function(claim_lottery_winner, claim) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      if(claim == 3) {
        $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/arbitrate/", {claim:claim, claim_message: $scope.claims.arbitratingClaim}).success(function(response) {
          $scope.getBet($stateParams.betId);
        }).error($scope.betAPIError);
      } else {
        $http.post($window.location.origin + "/api/v1/bets/" + $scope.bet.id + "/arbitrate/", {claim_lottery_winner: claim_lottery_winner, claim_message: $scope.claims.arbitratingClaim}).success(function(response) {
          $scope.getBet($stateParams.betId);
        }).error($scope.betAPIError);
      }
    };
    $scope.getResolvingDeadline = function() {
      var t = moment($scope.bet.event_deadline).add('days', 1).format();
      return t;
    };
    $scope.getResolvedDate = function() {
      if($scope.bet.resolved_at) {
        var t = moment($scope.bet.resolved_at).format('D/M/YYYY - HH:mm:ss');
        return t;
      } else {
        return false;
      }
    }
    $scope.getComplainingDeadline = function() {
      var t = moment($scope.bet.resolved_at).add('days', 1).format();
      return t;
    };
    $scope.getComplainedDate = function() {
      if($scope.bet.complained_at) {
        var t = moment($scope.bet.complained_at).format('D/M/YYYY - HH:mm:ss');
        return t;
      } else {
        return false;
      }
    }
    $scope.getArbitratingDeadline = function() {
      var t = moment($scope.bet.arbitrated_at).add('days', 1).format();
      return t;
    };
    $scope.getArbitratedDate = function() {
      if($scope.bet.arbitrated_at) {
        var t = moment($scope.bet.arbitrated_at).format('D/M/YYYY - HH:mm:ss');
        return t;
      } else {
        return false;
      }
    }
    $scope.bidComplained = function() {
      var i=0, len=$scope.bet.bids.length;
      for (; i<len; i++) {
        if ($scope.bet.bids[i].claim) {
          return $scope.bet.bids[i];
        }
      }
      return null;
    };
    $scope.isParticipant = function(userId) {
      var i=0, len=$scope.bet.bids.length;
      for (; i<len; i++) {
        if ($scope.bet.bids[i].participants.indexOf(userId) != -1) {
          return $scope.bet.bids[i];
        }
      }
      return null;
    };

    $scope.getBet($stateParams.betId);
  }])
  .controller('NewBetCtrl', ['$scope', '$http', '$timeout', '$rootScope', function($scope, $http, $timeout, $rootScope) {
    /*$scope.popover = function(element, text) {
      var showPopover = function () {
          $(element).popover('show');
      }
      , hidePopover = function () {
          $(element).popover('hide');
      };
      $(element)
          .popover({
           content: text,
           html: true,
           trigger: 'manual',
           template: '<div class="popover new-bet-tips"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content">Jajajajaj<p></p></div></div></div>',
          })
          .focus(showPopover)
          .blur(function () {
              $(this).popover('hide');
          });
    };

    $scope.popover("input#title", "eg: Messi will score a hat-trick tonight.");
    $scope.popover("textarea#description", "eg: If the game is cancelled I will declare this bet null");
    */
    $scope.betAPIError = function(response, status, headers, config) {
      $('#new-bet-fail-message').text(JSON.stringify(response));
      $('#new-bet-fail-modal').modal('show');
    };

    $scope.simpleBetBiddingDeadlineOptions = ['10 minutos',
                                              '20 minutos',
                                              '30 minutos',
                                              '45 minutos',
                                              '1 hora',
                                              '2 horas',
                                              '4 horas',
                                              '6 horas'];
    $scope.simpleBetEventDeadlineOptions = ['20 minutos',
                                            '30 minutos',
                                            '45 minutos',
                                            '1 hora',
                                            '2 horas',
                                            '4 horas',
                                            '6 horas',
                                            '12 horas',
                                            '24 horas'];

    $scope.inviteSelected = null;
    $scope.invites = [];

    $scope.noFocusStyles = {"height": "46px", "max-height": "46px", "overflow": "hidden", "min-height":"initial"};
    $scope.noFocusTextStyles = {"height": "34px"};
    $scope.transitionStyles = {"height": "auto", "max-height":"400px","transition":"1s"};
    $scope.transitionTitleStyles = {"height":"60px","transition":"1s"};
    //$scope.focusStyles = {"overflow":"visible", "min-height":"200px"};
    $scope.focusStyles = {"overflow":"visible"};

    $scope.resetWidget = function(new_bet) {
      $scope.newBetFormData = { bet_type: 1,
                        title: "",
                        amount: 10,
                        against: 10,
                        bidding_deadline: new Date(),
                        bidding_deadline_simple: '10 minutos',
                        event_deadline: new Date(),
                        event_deadline_simple: '2 horas',
                        public: true,
                        open_lottery: true};
      $scope.timeRelativeBidding = true;
      $scope.timeRelativeEvent = true;
      $scope.minBiddingDeadline = new Date();
      $scope.minEventDeadline = new Date();
      $scope.step = 1;
      $scope.show_comissions = false;
      $scope.selectedFriend = null;
      $scope.new_bet = null;
      if (!new_bet) {
        $scope.focus = false;
        $('.new-bet-widget').css($scope.noFocusStyles);
        $('#title').css($scope.noFocusTextStyles);
      }
      $('#description').css($scope.noFocusTextStyles);
    }
    $scope.resetWidget();

    $scope.expandWidget = function() {
      //$('.new-bet-widget').css({"height":"150px","transition":"0.8s"});
      $('.new-bet-widget').css($scope.transitionStyles);
      $('#title').css($scope.transitionTitleStyles);
      $scope.focus = true;
      $timeout(function() {
        $('.new-bet-widget').css($scope.focusStyles);
      }, 1000);
    }
    $scope.expandDescription = function() {
      $('#description').css({"height":"80px","transition":"1s"});
    }
    $scope.pot = function() {
      return $scope.newBetFormData.amount + $scope.newBetFormData.against;
    }
    $scope.getTypeName = function() {
      if($scope.newBetFormData.bet_type == 1) {
        return "Básica";
      } else if($scope.newBetFormData.bet_type == 2) {
        return "Subasta";
      } else {
        return "Porra";
      }
    }
    $scope.getRefereeFees = function() {
      if($scope.newBetFormData.bet_type == 1) {
        return Math.ceil($scope.pot()*0.02)*2;
      } else if($scope.newBetFormData.bet_type == 3) {
        return 6;
      } else {
        return "?";
      }
    }
    $scope.getWinningAmount = function() {
      if($scope.newBetFormData.bet_type == 1) {
        return $scope.pot() - Math.ceil($scope.pot()*0.02);
      } else {
        return "?";
      }
    }
    $scope.prevStep = function() {
      $scope.show_comissions = false;
      if($scope.step == 2) {
        $scope.step = 1;
      } else if($scope.step == 3) {
        $scope.step = 2;
      }
    }
    $scope.nextStep = function(bet_type) {
      $scope.show_comissions = false;
      if($scope.step == 1) {
        $scope.newBetFormData.bet_type = bet_type;
        $scope.step = 2;
      } else if($scope.step == 2) {
        if($scope.newBetFormData.public) {
          if($scope.postNewBet()) {
            $scope.step = 4;
          }
        } else {
          $scope.step = 3;
        }
      } else if($scope.step == 3) {
        if($scope.postNewBet()) {
          $scope.step = 4;
        }
      }
    }
    $scope.setPublic = function(pub) {
      $scope.newBetFormData.public = pub;
    }
    $scope.setOpenLottery = function(pub) {
      $scope.newBetFormData.open_lottery = pub;
    }

    $scope.biddingDeadlineCalendarOpened = false;
    $scope.openBiddingDeadlineCalendar = function($event) {
      $event.preventDefault();
      $event.stopPropagation();

      $scope.biddingDeadlineCalendarOpened = true;
    };

    $scope.eventDeadlineCalendarOpened = false;
    $scope.openEventDeadlineCalendar = function($event) {
      $event.preventDefault();
      $event.stopPropagation();

      $scope.eventDeadlineCalendarOpened = true;
    };

    $scope.relToAbsTime = function(rel) {
      var now = new Date();
      switch(rel) {
        case '10 minutos': now.setMinutes(now.getMinutes() + 10); break;
        case '20 minutos': now.setMinutes(now.getMinutes() + 20); break;
        case '30 minutos': now.setMinutes(now.getMinutes() + 30); break;
        case '45 minutos': now.setMinutes(now.getMinutes() + 45); break;
        case '1 hora': now.setMinutes(now.getMinutes() + 60); break;
        case '2 horas': now.setMinutes(now.getMinutes() + 60*2); break;
        case '4 horas': now.setMinutes(now.getMinutes() + 60*4); break;
        case '6 horas': now.setMinutes(now.getMinutes() + 60*6); break;
        case '12 horas': now.setMinutes(now.getMinutes() + 60*12); break;
        case '24 horas': now.setMinutes(now.getMinutes() + 60*24); break;
      }
      return now;
    }

    $scope.onSelectInvite = function($item, $model, $label) {
      if($model.id) {
        $scope.addInvite($model);
        $scope.inviteSelected = null;
      }
    }

    $scope.onInviteEnter = function(event) {
      if (!event || event.which == 13) {
        var usernames = $.map($rootScope.followers, function(element) { return element.username; });
        var i = usernames.indexOf($scope.inviteSelected);
        if(i != -1) {
          $scope.addInvite($rootScope.followers[i]);
        } else {
          $scope.addInvite($scope.inviteSelected);
        }
        $scope.inviteSelected = null;
      }
    }

    $scope.addInvite = function(inv) {
      if(inv && $scope.invites.indexOf(inv) == -1) {
        $scope.invites.push(inv);
        console.log($scope.invites);
      }
    }

    $scope.removeInvite = function(inv) {
      var index = $scope.invites.indexOf(inv);
      if(index != -1) {
        $scope.invites.splice(index, 1);
      }
    }

    $scope.postNewBet = function() {
      if(!$scope.newBetFormData['public'] && $scope.invites.length == 0) {
        $scope.betAPIError("En una apuesta privada tienes que invitar almenos una persona.");
        return false;
      }
      if($scope.newBetFormData['title'].length <= 0) {
        $scope.betAPIError("La apuesta es demasiado corta, por favor, pon un título más descriptivo.");
        return false;
      }
      var postData = jQuery.extend({}, $scope.newBetFormData);
      if (postData.bet_type == 1) {
        postData.odds = (postData.amount + postData.against) / postData.amount;
      }
      if($scope.timeRelativeBidding)
        postData.bidding_deadline = $scope.relToAbsTime(postData.bidding_deadline_simple);
      if($scope.timeRelativeEvent)
        postData.event_deadline = $scope.relToAbsTime(postData.event_deadline_simple);
      if(!postData.public) {
        postData['invites'] = $.map($scope.invites, function(element) { return element.username || element; });
      }
      
      delete postData.against;
      delete postData.bidding_deadline_simple;
      delete postData.event_deadline_simple;
      $http.post($window.location.origin + "/api/v1/bets/", postData)
      .success(function(response, status, headers, config) {
        $scope.new_bet = response;
        $scope.step = 5;
        $scope.invites = [];
      })
      .error(function(response, status, headers, config) {
        $scope.betAPIError(response, status, headers, config);
        //$scope.new_bet = response;
        //$scope.step = 5;
        //$scope.invites = [];
      });
      return true;
    };
  }])
  .controller('MainCtrl', ['$scope', '$http', function($scope, $http) {
    
  }]);
