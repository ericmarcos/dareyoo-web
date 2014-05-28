
'use strict';

/* Controllers */

angular.module('dareyoo.controllers', []).
  controller('EditProfileCtrl', ['$scope', '$http', '$location', '$routeParams', 'config', 'blob', function($scope, $http, $location, $routeParams, config, blob) {
    $scope.new_user = $location.search('new');
    $scope.upload_state = 'initial';
    if($scope.user) {
      $scope.new_email = $scope.user.email;
      $scope.new_username = $scope.user.username;
      $scope.new_description = $scope.user.description;
    } else {
      $scope.$watch('user', function() {
        if($scope.user) {
          $scope.new_email = $scope.user.email;
          $scope.new_username = $scope.user.username;
          $scope.new_description = $scope.user.description;
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
      $http.post("/api/v1/users/" + $scope.user.id + "/pic_upload/", fd, {
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
      console.log("desc: " + $scope.new_description);
      $http.put("/api/v1/users/" + $scope.user.id + "/", {
          email: $scope.new_email,
          username: $scope.new_username,
          description: $scope.new_description
      }).success(function(response){
        if($scope.new_user) {
          $scope.$state.go("who-to-follow");
        }
      }).error(function(response){
        console.log(response);
      });
    };
  }]).
  controller('WhoToFollowCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.provider = '';
    $scope.friends_list = [];
    $scope.search_friends = function(provider) {
      $scope.provider = provider;
      var url = "/api/v1/search-dareyoo-suggested/";
      if(provider == 'facebook')
        url = "/api/v1/search-facebook-friends/";
      $http.get(url).success(function(response) {
        if(response.results) $scope.friends_list = response.results;
        else $scope.friends_list = response;
      });
    };
  }]).
  controller('RankingCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.ranking = [];
    $scope.getRanking = function(order) {
      $http.get("/api/v1/ranking/").success(function(response) {
        if(response.results) $scope.ranking = response.results;
        else $scope.ranking = response;
      });
    }

    $scope.getRanking();
  }]).
  controller('TimelineCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get("/api/v1/timeline/", {'params': {'order': order}}).success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    }

    $scope.getTimeline();
  }]).
  controller('TimelineGlobalCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get("/api/v1/timeline/", {'params': {'order': order, 'global': true}}).success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    }

    $scope.getTimeline();
  }]).
  controller('TimelineConflictsCtrl', ['$scope', '$http', '$location', '$filter', function($scope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get("/api/v1/timeline/", {'params': {'order': order, 'global': true, 'state': 'arbitrating'}}).success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    }

    $scope.getTimeline();
  }]).
  controller('SearchCtrl', ['$scope', '$rootScope', function($scope, $rootScope) {
    //$rootScope.q = "Euro";
    $scope.search = function() {
      $rootScope.$state.go("main.timeline-search", {}, {"reload": true});
    }
  }]).
  controller('TimelineSearchCtrl', ['$scope', '$rootScope', '$http', '$location', '$filter', function($scope, $rootScope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";
    $scope.getTimeline = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get("/api/v1/bets/search/", {'params': {'q': $rootScope.q.query}}).success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    }

    $scope.getTimeline();
  }]).
  controller('OpenBetsCtrl', ['$scope', '$rootScope', '$http', '$location', '$filter', function($scope, $rootScope, $http, $location, $filter) {
    $scope.bets = [];
    $scope.more_bets_link = "";
    $scope.order_by = "-created_at";

    $scope.getOpenBets = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get("/api/v1/open-bets/").success(function(response) {
        if(response.results) $scope.bets = response.results;
        else $scope.bets = response;
        $scope.loaded = true;
      });
    };
    $scope.getOpenBets();
  }])
  .controller('UserCtrl', ['$scope', '$rootScope', '$http', '$stateParams', function($scope, $rootScope, $http, $stateParams) {
    $scope.profile_user_follows_me = false;
    $scope.i_follow_profile_user = false;
    $scope.followers = [];
    $scope.following = [];

    $scope.getUser = function(id) {
      $http.get("/api/v1/users/" + id).success(function(response) {
        $scope.profile_user = response;
      });
    };
    $scope.getNBets = function(id, params, callback) {
      params = params || {};
      callback = callback || function(response) { $scope.n_bets = response.count; };
      $http.get("/api/v1/users/" + id + "/n_bets/", {'params': params}).success(callback);
    }
    $scope.followUser = function(id) {
      $http.post("/api/v1/users/" + id + "/follow/").success(function(response) {
        $scope.$broadcast('follow_unfollow');
      });
    };
    $scope.unfollowUser = function(id) {
      $http.post("/api/v1/users/" + id + "/unfollow/").success(function(response) {
        $scope.$broadcast('follow_unfollow');
        //$scope.loadUser();
      });
    };
    $scope.isFollowing = function(id, ask_id, success) {
      $http.get("/api/v1/users/" + id + "/is_following/", {'params': {'user_id': ask_id}}).success(success);
    };
    $scope.loadUser = function() {
      var id = $stateParams.userId;
      $scope.getUser(id);
      $scope.getNBets(id);
      if($rootScope.user) {
        $scope.isFollowing(id, $rootScope.user.id, function(response) {
          $scope.profile_user_follows_me = response.status;
        });
        $scope.isFollowing($rootScope.user.id, id, function(response) {
          $scope.i_follow_profile_user = response.status;
        });
      }
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
      $http.get("/api/v1/users/" + id + "/followers/").success(function(response) {
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
      $http.get("/api/v1/users/" + id + "/following/").success(function(response) {
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
      $http.get("/api/v1/users/" + id + "/bets/", {'params': params}).success(callback);
    };

    $scope.getBets($stateParams.userId);
  }])
  .controller('BetCtrl', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {
    $scope.loaded = false;
    $scope.bidTitle = "";
    $scope.bidAmount = 10;

    $scope.betAPIError = function(response, status, headers, config) {
        $('#bet-fail-message').text(JSON.stringify(response));
        $('#bet-fail-modal').modal('show');
      };

    $scope.getBet = function(id) {
      $http.get("/api/v1/bets/" + id).success(function(response) {
        $scope.bet = response;
        $scope.loaded = true;
      }).error($scope.betAPIError);
    };
    $scope.acceptBet = function() {
      $http.post("/api/v1/bets/" + $scope.bet.id + "/accept_bet/").success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.postBid = function(title, amount) {
      $http.post("/api/v1/bets/" + $scope.bet.id + "/bids/", {title: title, amount: amount}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.acceptBid = function(bidId) {
      $http.post("/api/v1/bets/" + $scope.bet.id + "/accept_bid/", {bid_id: bidId}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.removeBid = function(bidId) {
      console.log(bidId);
      $http.post("/api/v1/bets/" + $scope.bet.id + "/remove_bid/", {bid_id: bidId}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.resolveBet = function(claim, message) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      $http.post("/api/v1/bets/" + $scope.bet.id + "/resolve/", {claim: claim, claim_message: message}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.complainBet = function(bid_id, claim, message) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      $http.post("/api/v1/bids/" + bid_id + "/complain/", {claim: claim, claim_message: message}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };
    $scope.arbitrateBet = function(claim, message) { /* {1: Bet author won, 2: Bid author won, 3: null} */
      $http.post("/api/v1/bets/" + $scope.bet.id + "/arbitrate/", {claim: claim, claim_message: message}).success(function(response) {
        $scope.getBet($stateParams.betId);
      }).error($scope.betAPIError);
    };

    $scope.getBet($stateParams.betId);
  }])
  .controller('NewBetCtrl', ['$scope', '$http', function($scope, $http) {
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
    $scope.newBetFormData = { bet_type: 1,
                        amount: 10,
                        against: 10,
                        bidding_deadline: new Date(),
                        bidding_deadline_simple: '10 minutos',
                        event_deadline: new Date(),
                        event_deadline_simple: '2 horas',
                        public: true};
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

    $scope.minBiddingDeadline = new Date();
    $scope.minEventDeadline = new Date();

    $scope.timeRelativeBidding = true;
    $scope.timeRelativeEvent = true;
    $scope.step = 1;
    $scope.focus = false;
    
    $scope.selectedCountry = null;
    $scope.countries = {'sumadors':'torneo', 'Josep':'amigo', 'Jaume':'amigo'};



    $scope.expandWidget = function() {
      //$('.new-bet-widget').css({"height":"150px","transition":"0.8s"});
      $('.new-bet-widget').css({"max-height":"300px","transition":"1s"});
      $scope.focus = true;
    }
    $scope.prevStep = function() {
      if($scope.step == 2) {
        $scope.step = 1;
      } else if($scope.step == 3) {
        $scope.step = 2;
      }
    }
    $scope.nextStep = function(bet_type) {
      if($scope.step == 1) {
        $scope.newBetFormData.bet_type = bet_type;
        $scope.step = 2;
      } else if($scope.step == 2) {
        $scope.step = 3;
      } else if($scope.step == 3) {
        $scope.step = 4;
      }
    }
    $scope.setPublic = function(pub) {
      $scope.newBetFormData.public = pub;
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
        case '1 horas': now.setMinutes(now.getMinutes() + 60); break;
        case '2 horas': now.setMinutes(now.getMinutes() + 60*2); break;
        case '4 horas': now.setMinutes(now.getMinutes() + 60*4); break;
        case '6 horas': now.setMinutes(now.getMinutes() + 60*6); break;
        case '12 horas': now.setMinutes(now.getMinutes() + 60*12); break;
        case '24 horas': now.setMinutes(now.getMinutes() + 60*24); break;
      }
    }

    $scope.postNewBet = function() {
      var postData = jQuery.extend({}, $scope.newBetFormData);
      if (postData.bet_type == 1) {
        postData.odds = (postData.amount + postData.against) / postData.amount;
      } else if(postData.bet_type == 2) {

      }
      if($scope.timeRelative) {
        postData.bidding_deadline = $scope.relToAbsTime(postData.bidding_deadline_simple);
        postData.event_deadline = $scope.relToAbsTime(postData.event_deadline_simple);
      }
      delete postData.against;
      delete postData.bidding_deadline_simple;
      delete postData.event_deadline_simple;
      $http.post("/api/v1/bets/", postData)
      .success(function(response, status, headers, config) {
        $('#new-bet-steps li:eq(3) a').tab('show');
        //$scope.bets = response.results;
        //$scope.loaded = true;
      })
      .error(function(response, status, headers, config) {
        $('#new-bet-fail-message').text(JSON.stringify(response));
        $('#new-bet-fail-modal').modal('show');
      });
    };
  }])
  .controller('MainCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.n_open_bets = 0;
    $scope.newBetView = function() {
      return $scope.$state.includes('main.new-bet') || $scope.$state.includes('main.new-bet-simple') ||
      $scope.$state.includes('main.new-bet-auction') || $scope.$state.includes('main.new-bet-lottery');
    }
    $scope.getNOpenBets = function(order) {
      $scope.order_by = order || $scope.order_by;
      $http.get("/api/v1/open-bets/").success(function(response) {
        if(response.results) $scope.n_open_bets = response.count;
        else $scope.n_open_bets = response.length;
      });
    };
    
    $scope.getNOpenBets();
  }]);
