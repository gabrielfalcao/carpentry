angular.module('JaciApp.ShowBuilder', ['JaciApp.Common']).controller('ShowBuilderController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {

    var builderId = $stateParams.builder_id;
    $rootScope.builder = $rootScope.builders[builderId];
    if ($rootScope.buildCache[builderId] === undefined) {
        $rootScope.buildCache[builderId] = {};
    }

    function refresh() {
        $http
            .get('/api/builder/' + $rootScope.builder.id + '/builds')

            .success(function(data, status, headers, config) {
                $rootScope.buildCache[builderId] = data;
                $scope.builds = data;
            })

            .error(function(data, status, headers, config) {
                console.log("FAILED", data);
                clearInterval(poller);
                $rootScope.go("/");
            });
    }
    $scope.refresh = refresh;

    var poller = setInterval(function () {
        if ($scope.eof) {
            clearInterval(poller);
        }
        refresh();
    }, 750);
});
