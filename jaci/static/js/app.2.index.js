angular.module("JaciApp.Index", [
    "JaciApp.Common",
]).controller('IndexController', function($rootScope, $scope, $state, $http, $cookies, hotkeys, notify){
    hotkeys.add({
        combo: 'ctrl+n',
        description: 'create a new project',
        callback: function(){
            $rootScope.fo("/new-project");
        }
    });
});
