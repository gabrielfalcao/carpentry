angular.module("JaciApp", [
    "ngCookies",
    "ui.router",
    "cfp.hotkeys",
    "cgNotify",
    "JaciApp.Common",
    "JaciApp.Index",
]).config(function($stateProvider, $urlRouterProvider) {
    $stateProvider
        .state("index", {
            url: "/index",
            templateUrl: "/assets/js/templates/index.html",
            controller: "IndexController"
        })
        .state("not-found", {
            url: "/not-found",
            templateUrl: "/assets/js/templates/404.html"
        });
    $urlRouterProvider.otherwise("index");

}).run(function($rootScope, $state, $templateCache, $http, notify){
    $rootScope.$state = $state;
    $rootScope.$on("$viewContentLoaded", function() {
        $templateCache.removeAll();
    });
    notify.config({
        "templateUrl": "/assets/vendor/angular-notify/angular-notify.html"
    });
})
.controller("JaciMainCtrl", function($scope, $http){
});
