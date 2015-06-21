angular.module('JaciApp.EditBuilder', ['JaciApp.Common']).controller('EditBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify, $stateParams) {

    var builderId = $stateParams.builder_id;
    $scope.builder = $rootScope.builders[builderId];

    $scope.loadBuilder = function(){
        $http.get('/api/builder/' + builderId)
            .success(function(data, status, headers, config) {
                console.log("BUIDLER", data);
                $scope.builder = data;
                $rootScope.go("/builder/" + builderId);

            })

            .error(function(data, status, headers, config) {
                console.log("Failed to load builder for editing", data);
                $rootScope.go("/");
            });
    };

    $scope.editBuilder = function(builder){
        $http.put('/api/builder/' + $scope.builder.id, builder)
            .success(function(data, status, headers, config) {
                console.log("PUT BUILDER", data);
                $scope.builder = data;
            })

            .error(function(data, status, headers, config) {
                console.log("Failed to edit builder", builder, data, status);
            });
    };
});
