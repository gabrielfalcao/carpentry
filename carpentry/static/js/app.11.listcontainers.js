angular.module('CarpentryApp.ListDockerContainers', ['CarpentryApp.Common']).controller('ListDockerContainersController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {
    $rootScope.resetPollers();

    $rootScope.getDockerContainers();


    var limit = 720;
    var counter = 0;
    $rootScope.resetPollers();
    $rootScope.refreshDockerContainersPoller = setInterval(function(){
        counter++;
        if (counter > 720) {
            clearInterval($rootScope.refreshDockerContainersPoller);
        }
        $rootScope.getDockerContainers();
    }, 1000);

});
