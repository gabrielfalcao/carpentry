angular.module("JaciApp", [
    "ngCookies",
    "ui.router",
    "cfp.hotkeys",
    "cgNotify",
    "JaciApp.Common",
    "JaciApp.Index",
    "JaciApp.NewBuilder",
    "JaciApp.Build",
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
        .state("build-detail", {
            url: "/build/:owner/:project/:buildid",
            templateUrl: "/assets/js/templates/build-detail.html",
            controller: "BuildController"
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
.directive('navbar', function($rootScope, $state, $location) {
    $rootScope.go = function ( path ) {
        $location.path( path );
    };
    return {
        restrict: 'E',
        templateUrl: "/assets/js/templates/navbar.html",
        link: function (scope, element, attrs) {
        }
    }
})
.controller("JaciMainCtrl", function($scope, $http){
});
