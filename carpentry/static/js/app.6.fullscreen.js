angular.module('CarpentryApp.Fullscreen', ['CarpentryApp.Common']).controller('FullscreenController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    $rootScope.resetPollers();
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
