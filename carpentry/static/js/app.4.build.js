angular.module('CarpentryApp.Build', ['CarpentryApp.Common']).controller('BuildController', function ($rootScope, $scope, $state, $http, $sce, notify, $stateParams) {
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

    $scope.html_output = null;
    function get_build() {
        if (!$stateParams.build_id) {
            console.log("Invalid build id:", $stateParams);
            return;
        }
        var url = '/api/build/'+$stateParams.build_id;
        $http.get(url).success(function (data, status, headers, config) {
            $scope.build = data;
            $scope.html_output = $sce.trustAsHtml(data.stdout);
            console.log(data);
        }).error(function (data, status, headers, config) {
            if (!status) {
                console.log("server did not respond to" + url);
                return;
            }
            notify('failed to retrieve build: '+ status)
            console.log('failed ' + url, status);
            clearInterval(poller);
            $scope.html_output = null;
            $rootScope.go("/")
        });

    }
    // function get_output() {
    //     var url = '/api/build/'+$stateParams.build_id+'/output'
    //     $http.get(url).success(function (data, status, headers, config) {
    //         $scope.html_output = $sce.trustAsHtml(data.stdout);
    //     }).error(function (data, status, headers, config) {
    //         console.log('failed ' + url, status);
    //         $scope.html_output = $sce.trustAsHtml(url + ' failed: ' + status);
    //         clearInterval(poller);
    //         $rootScope.defaultErrorHandler(data, status, headers, config);
    //     });
    // }

    // function refresh(){
    //     get_build();
    //     get_output();
    // }

    // $scope.refresh = refresh;
    var limit = 720;
    var counter = 0;

    $rootScope.resetPollers();
    $rootScope.buildPoller = setInterval(function(){
        counter++;
        if (counter > 720) {
            clearInterval($rootScope.buildPoller);
        }
        get_build();
    }, 500);
    get_build();
});
