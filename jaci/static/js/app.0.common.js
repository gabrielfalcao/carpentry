angular.module("JaciApp.Common", [
]).directive('navbar', function($rootScope, $state, $location) {
    $rootScope.go = function ( path ) {
        $location.path( path );
    };
    return {
        restrict: 'E',
        templateUrl: "/assets/js/templates/navbar.html",
        link: function (scope, element, attrs) {
        }
    }
});
