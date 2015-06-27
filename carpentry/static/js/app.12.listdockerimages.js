angular.module('CarpentryApp.ListDockerImages', ['CarpentryApp.Common']).controller('ListDockerImagesController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {
    $rootScope.resetPollers();

    $rootScope.getDockerImages();

    $scope.removeImage = function(image){
        var url = "/api/docker/image/" + image.Id + "/remove";
        $http.post(url).success(function (data, status, headers, config) {
            notify('image successfully removed');
            $rootScope.getDockerImages();
        }).error(function (data, status, headers, config) {
            notify('failed to remove image ' + image.Names[0]);
            $rootScope.getDockerImages();
        });
    };

});
