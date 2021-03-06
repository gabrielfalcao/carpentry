angular.module('CarpentryApp.ShowBuilder', ['CarpentryApp.Common']).controller('ShowBuilderController', function ($rootScope, $scope, $state, $http, $location, hotkeys, notify, $stateParams) {

    var builderId = $stateParams.builder_id;
    $rootScope.builder = $rootScope.builders[builderId];
    if ($rootScope.buildCache[builderId] === undefined) {
        $rootScope.buildCache[builderId] = {};
    }


    function refresh() {
        if ($rootScope.builder.id === undefined) {
            $rootScope.go('/');
            return
        }
        var url = '/api/builder/' + $rootScope.builder.id + '/builds';
        $http
            .get(url)

            .success(function(data, status, headers, config) {
                $rootScope.buildCache[builderId] = data;
                $scope.builds = data;
            })

            .error(function(data, status, headers, config) {
                if (!status) {
                    console.log("Server did not respond to " + url);
                    return;
                }
                if (status !== 502) {
                    notify('failed to retreve builder info');
                }
                console.log("failed to retreve builder info", data);
                clearInterval(poller);
            });
    }
    $scope.refresh = refresh;
    $scope.clearBuilds = function(builder){
        $http
            .delete('/api/builder/' + $rootScope.builder.id + '/builds')
            .success(function(data, status, headers, config) {
                notify(data.total + " builds deleted");
            })

            .error(function(data, status, headers, config) {
                console.log('failed to clear builds from ' + $rootScope.builder.name);
                return;
                notify('failed to clear builds from ' + $rootScope.builder.name);
            });
    };
    var limit = 720;
    var counter = 0;
    $rootScope.resetPollers();
    $rootScope.builderPoller = setInterval(function(){
        counter++;
        if (counter > 720) {
            clearInterval($rootScope.builderPoller);
        }
        refresh();
    }, 1000);
});
