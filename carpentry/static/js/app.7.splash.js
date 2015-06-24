angular.module('CarpentryApp.Splash', ['CarpentryApp.Common']).controller('SplashController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    $rootScope.resetPollers();

    if ($rootScope.isAuthenticated) {
        $rootScope.go('/');
    }
});
