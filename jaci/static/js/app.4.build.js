angular.module('JaciApp.Build', ['JaciApp.Common']).controller('BuildController', function ($rootScope, $scope, $state, $http, $sce, notify, $stateParams) {
    $scope.html_output = $sce.trustAsHtml('loading...');
    var builderId = $stateParams.builder_id;
    $rootScope.builder = $rootScope.builders[builderId];
    $scope.build_id = $stateParams.build_id;
    $scope.eof = false;

    if ($rootScope.buildCache[builderId] === undefined) {
        $rootScope.buildCache[builderId] = {}
    }
    if ($rootScope.buildCache[builderId][$stateParams.build_id] === undefined) {
        $rootScope.buildCache[builderId][$stateParams.build_id] = {}
    }
    var build =  $rootScope.buildCache[builderId][$scope.build_id];

    $scope.html_output = $sce.trustAsHtml(build.stdout || "");

    function get_build() {
        var url = '/api/build/'+$stateParams.build_id;
        $http.get(url).success(function (data, status, headers, config) {
            $scope.build = data;
            console.log(data);
        }).error(function (data, status, headers, config) {
            console.log('failed ' + url, status);
            clearInterval(poller);
            $scope.html_output = $sce.trustAsHtml(url + ' failed: ' + status);
            $rootScope.go("/");

        });

    }
    function get_output() {
        var url = '/api/build/'+$stateParams.build_id+'/output'
        $http.get(url).success(function (data, status, headers, config) {
            $scope.html_output = $sce.trustAsHtml(data.stdout);
        }).error(function (data, status, headers, config) {
            console.log('failed ' + url, status);
            $scope.html_output = $sce.trustAsHtml(url + ' failed: ' + status);
            clearInterval(poller);
            $rootScope.go("/");
        });
    }

    function refresh(){
        get_build();
        get_output();
    }

    $scope.refresh = refresh;
    var limit = 720;
    var counter = 0;
    var poller = setInterval(function(){
        counter++;
        if (counter > 720) {
            clearInterval(poller);
        }
        refresh();
    }, 500);


    refresh();

});
