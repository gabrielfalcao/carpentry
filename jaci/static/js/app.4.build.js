angular.module('JaciApp.Build', ['JaciApp.Common']).controller('BuildController', function ($rootScope, $scope, $state, $http, $sce, notify, $stateParams) {
    $scope.html_output = $sce.trustAsHtml('loading...');
    var builderId = $stateParams.builder_id;
    $scope.builder = $rootScope.builders[builderId];
    $scope.build_id = $stateParams.build_id;
    $scope.eof = false;
    var last_build_output = "";
    if ($rootScope.buildCache[builderId] === undefined) {
        $rootScope.buildCache[builderId] = {}
    }
    if ($rootScope.buildCache[builderId][$stateParams.build_id] === undefined) {
        $rootScope.buildCache[builderId][$stateParams.build_id] = {}
    }
    var build =  $rootScope.buildCache[builderId][$scope.build_id];

    $scope.html_output = $sce.trustAsHtml(build.stdout || "");

    function get_output() {
        var url = '/api/build/'+$stateParams.build_id+'/output'
        $http.get(url).success(function (data, status, headers, config) {
            if (data.stdout === last_build_output) {
                $scope.eof = true;
            } else {
                $scope.html_output = $sce.trustAsHtml(data.stdout);
                last_build_output = data.stdout;
            }
            $scope.build = data;
        }).error(function (data, status, headers, config) {
            console.log('failed ' + url, status);
            $scope.html_output = $sce.trustAsHtml(url + ' failed: ' + status);
        });
    }

    var poller = setInterval(function () {
        if ($scope.eof) {
            clearInterval(poller);
        }
        get_output();
    }, 1000);
});
