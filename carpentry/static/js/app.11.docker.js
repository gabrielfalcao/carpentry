angular.module('CarpentryApp.Docker', ['CarpentryApp.Common']).controller('DockerController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {
    $rootScope.resetPollers();

    $rootScope.getDockerImages();

    $scope.stopContainer = function(container){
        var url = "/api/docker/container/" + container.Id + "/stop";
        $http.post(url).success(function (data, status, headers, config) {
            notify('container successfully stopped');
        }).error(function (data, status, headers, config) {
            notify('failed to remove container ' + container.Names[0]);
        });
    };
    $scope.removeContainer = function(container){
        var url = "/api/docker/container/" + container.Id + "/remove";
        $http.post(url).success(function (data, status, headers, config) {
            notify('container successfully removed');
        }).error(function (data, status, headers, config) {
            notify('failed to remove container ' + container.Names[0]);
        });
    };

    $scope.removeImage = function(image){
        var url = "/api/docker/image/" + image.Id + "/remove";
        $http.post(url).success(function (data, status, headers, config) {
            notify('image successfully removed');

        }).error(function (data, status, headers, config) {
            notify('failed to remove image ' + image.Names[0]);
        });
    };

    $scope.dockerPull = function(dockerPullInfo){
        var url = "/api/docker/pull";
        $http.post(url, dockerPullInfo).success(function (data, status, headers, config) {
            notify('image successfully pull');
        }).error(function (data, status, headers, config) {
            notify('failed to remove image ' + image.Names[0]);
        });
    };

    $scope.dockerRun = function(dockerRunInfo){
        var url = "/api/docker/run";
        $http.post(url, dockerRunInfo).success(function (data, status, headers, config) {
            notify('image successfully run');
        }).error(function (data, status, headers, config) {
            notify('failed to remove image ' + image.Names[0]);
        });
    };

    var limit = 720;
    var imageCounter = 0;

    $rootScope.refreshDockerImagesPoller = setInterval(function(){
        imageCounter++;
        if (imageCounter > 720) {
            clearInterval($rootScope.refreshDockerImagesPoller);
        }
        $rootScope.getDockerImages();
    }, 1000);


    var limit = 720;
    var containerCounter = 0;

    $rootScope.refreshDockerContainersPoller = setInterval(function(){
        containerCounter++;
        if (containerCounter > 720) {
            clearInterval($rootScope.refreshDockerContainersPoller);
        }
        $rootScope.getDockerContainers();
    }, 1000);

});
