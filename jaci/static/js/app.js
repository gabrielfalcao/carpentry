angular.module("JaciApp", [
    "ngCookies",
    "ui.router",
    "cfp.hotkeys",
    "cgNotify",
    "JaciApp.Common",
    "JaciApp.Index",
    "JaciApp.NewBuilder",
]).config(function($stateProvider, $urlRouterProvider) {
    $stateProvider
        .state("index", {
            url: "/index",
            templateUrl: "/assets/js/templates/index.html",
            controller: "IndexController"
        })
        .state("new-builder", {
            url: "/new-builder",
            templateUrl: "/assets/js/templates/new-builder.html",
            controller: "NewBuilderController"
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
    $('pre code').each(function(i, block) {
        hljs.highlightBlock(block);
    });

})
    .controller("JaciMainCtrl", function($scope, $http){
    });
