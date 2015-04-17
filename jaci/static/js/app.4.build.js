angular.module("JaciApp.Build", [
    "JaciApp.Common",
]).controller('BuildController', function($rootScope, $scope, $state, $http, $cookies, hotkeys, notify, $routeParams){
    $scope.build_id = $routeParams.buildid;
    $scope.project = {
        "owner": $routeParams.owner,
        "name": $routeParams.project
    };
});
