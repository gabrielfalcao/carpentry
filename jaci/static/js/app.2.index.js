angular.module('JaciApp.Index', ['JaciApp.Common']).controller(
    'IndexController',
    function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {

        var limit = 720;
        var counter = 0;
        $rootScope.resetPollers();
        $rootScope.indexPoller = setInterval(function(){
            counter++;
            if (counter > 720) {
                clearInterval($rootScope.indexPoller);
            }
            $rootScope.refresh();
        }, 1000);
        $rootScope.refresh();
});
