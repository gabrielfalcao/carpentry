angular.module('JaciApp.Index', ['JaciApp.Common']).controller(
    'IndexController',
    function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {

        var limit = 720;
        var counter = 0;
        var poller = setInterval(function(){
            counter++;
            if (counter > 720) {
                clearInterval(poller);
            }
            $rootScope.refresh();
        }, 500);
        $rootScope.refresh();
});
