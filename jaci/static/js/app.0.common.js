angular.module("JaciApp.Common", [
]).directive('navbar', function($rootScope, $state) {
    return {
        restrict: 'E',
        templateUrl: "/assets/js/templates/navbar.html",
        link: function (scope, element, attrs) {
        }
    }
});
