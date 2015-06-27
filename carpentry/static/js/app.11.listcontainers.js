angular.module('CarpentryApp.ListDockerContainers', ['CarpentryApp.Common']).controller('ListDockerContainersController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {
    $rootScope.resetPollers();

    $rootScope.getDockerContainers();

    $scope.stopContainer = function(container){
        var url = "/api/docker/container/" + container.Id + "/stop";
        $http.post(url).success(function (data, status, headers, config) {
            notify('container successfully stopped');
            $rootScope.getDockerContainers();
        }).error(function (data, status, headers, config) {
            notify('failed to remove container ' + container.Names[0]);
            $rootScope.getDockerContainers();
        });
    };
    $scope.removeContainer = function(container){
        var url = "/api/docker/container/" + container.Id + "/remove";
        $http.post(url).success(function (data, status, headers, config) {
            notify('container successfully removed');
            $rootScope.getDockerContainers();
        }).error(function (data, status, headers, config) {
            notify('failed to remove container ' + container.Names[0]);
            $rootScope.getDockerContainers();
        });
    };
});
