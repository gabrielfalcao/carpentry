angular.module('CarpentryApp.EditBuilder', ['CarpentryApp.Common']).controller('EditBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify, $stateParams) {

    var builderId = $stateParams.builder_id;
    $scope.builder = $rootScope.builders[builderId];
    $rootScope.resetPollers();
    $scope.saveInProcess = false;

    $scope.loadBuilder = function(){
        $http.get('/api/builder/' + builderId)
            .success(function(data, status, headers, config) {
                console.log("BUIDLER", data);
                $scope.builder = data;
                $rootScope.go("/builder/" + builderId);

            })

            .error(function(data, status, headers, config) {
                if (status !== 502) {
                    notify('Failed to load builder for editing');
                }


                console.log("Failed to load builder for editing", data);
                $rootScope.go("/");
            });
    };

    $scope.editBuilder = function(builder){
        $scope.saveInProcess = true;
        $http.put('/api/builder/' + $scope.builder.id, builder)
            .success(function(data, status, headers, config) {
                notify($scope.builder.name +' saved successfully');
                $scope.builder = data;
                $scope.saveInProcess = false;

            })

            .error(function(data, status, headers, config) {
                $scope.saveInProcess = false;
                if (status !== 502) {
                    notify('Failed to edit builder');
                }
                console.log("Failed to edit builder", builder, data, status);
            });
    };
    $scope.deleteBuilder = function(builder){
        $scope.saveInProcess = true;
        $http.delete('/api/builder/' + $scope.builder.id)
            .success(function(data, status, headers, config) {
                notify($scope.builder.name +' deleted successfully');
                $scope.builder = data;
                $rootScope.go('/');
                $scope.saveInProcess = false;
            })

            .error(function(data, status, headers, config) {
                notify('Failed to delete builder');
                console.log("Failed to delete builder", builder, data, status);
                $scope.saveInProcess = false;
            });
    };

});
