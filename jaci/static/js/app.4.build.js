angular.module('JaciApp.Build', ['JaciApp.Common']).controller('BuildController', function ($rootScope, $scope, $state, $http, $sce, notify, $stateParams) {
    $scope.html_output = $sce.trustAsHtml('loading...');
    var builderId = $stateParams.builder_id;
    $scope.builder = $rootScope.builders[builderId];
    $scope.build_id = $stateParams.build_id;

    function get_output() {
        var url = '/api/build/'+$stateParams.build_id+'/output'
        $http.get(url).success(function (data, status, headers, config) {
            $scope.html_output = $sce.trustAsHtml(data.stdout);
        }).error(function (data, status, headers, config) {
            console.log('failed ' + url, status);
            $scope.html_output = $sce.trustAsHtml(url + ' failed: ' + status);
        });
    }
    var poller = setInterval(function () {
        if ($scope.build.done) {
            clearInterval(poller);
        }
        get_output();
    }, 1000);
});
