angular.module('JaciApp.Splash', ['JaciApp.Common']).controller('SplashController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    if ($rootScope.isAuthenticated) {
        $rootScope.go('/');
    }
});
