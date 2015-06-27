angular.module('CarpentryApp.ListDockerImages', ['CarpentryApp.Common']).controller('ListDockerImagesController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {
    $rootScope.resetPollers();

    $rootScope.getDockerImages();
});
