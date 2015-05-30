angular.module('JaciApp.Build', ['JaciApp.Common']).controller('BuildController', function ($rootScope, $scope, $state, $http, $sce, notify, $stateParams) {
  $rootScope.build_id = $stateParams.buildid;
  $rootScope.project = {
    'owner': $stateParams.owner,
    'name': $stateParams.project
  };
  $scope.html_output = $sce.trustAsHtml('loading...');
  $scope.build = {};
  function get_output() {
    // var url = "/build/" + $stateParams.owner +
    //           "/" + $stateParams.project +
    //           "/" + $stateParams.buildid +
    //     "/output";
    var url = '/build/' + $stateParams.owner + '/' + $stateParams.project + '/';
    $http.get(url).success(function (data, status, headers, config) {
      $scope.html_output = $sce.trustAsHtml(data.stdout);
      $scope.build = data.build || {};
    }).error(function (data, status, headers, config) {
      console.log('failed ' + url, status);
      $scope.build = { 'stdout': 'error:' + status };
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