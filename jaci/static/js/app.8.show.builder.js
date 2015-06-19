angular.module('JaciApp.ShowBuilder', ['JaciApp.Common']).controller('ShowBuilderController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {

    var builderId = $stateParams.builder_id;
    $scope.builder = $rootScope.builders[builderId];
    $rootScope.buildCache[builderId] = [];

    $rootScope.triggerBuild = function(){
        console.log( "triggerBuild");
        $http
            .post('/api/builder/' + $scope.builder.id + '/build')

        .success(function(data, status, headers, config) {
            $rootScope.go('/builder/' + builderId + '/build/' + data.id);
        })

        .error(function(data, status, headers, config) {
            console.log("FAILED", data);
        });

    };

        $http
            .get('/api/builder/' + $scope.builder.id + '/builds')

        .success(function(data, status, headers, config) {
            $rootScope.buildCache[builderId] = data;
            $scope.builds = data;
        })

        .error(function(data, status, headers, config) {
            console.log("FAILED", data);
        });
});
