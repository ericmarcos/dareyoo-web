//sudo npm install --save-dev gulp yargs gulp-if gulp-uglify gulp-size gulp-less gulp-rename gulp-replace gulp-git gulp-s3 gulp-clean

var gulp = require('gulp');
var args   = require('yargs').argv;
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var size = require('gulp-size');
var less = require('gulp-less');
var rename = require("gulp-rename");
var replace = require("gulp-replace");
var git = require("gulp-git");
var s3 = require("gulp-s3");
var clean = require("gulp-clean");
var print = require("gulp-print");

var isPro = args.pro;
var isPre = args.pre;

var paths = {
  html: ['./static/beta/partials/**'],
  scripts: ['./static/beta/js/ng-time-relative.js',
            './static/beta/js/services.js',
            './static/beta/js/directives.js',
            './static/beta/js/controllers.js',
            './static/beta/js/app.js'],
  scripts_libs: ['./static/beta/lib/jquery/dist/jquery.min.js',
                './static/beta/lib/bootstrap/dist/js/bootstrap.min.js',
                './static/beta/lib/angular/angular.min.js',
                './static/beta/lib/angular-bootstrap/ui-bootstrap-tpls.min.js',
                './static/beta/lib/angular-ui-router/release/angular-ui-router.min.js',
                './static/beta/lib/angular-cookies/angular-cookies.min.js',
                './static/beta/lib/momentjs/min/moment-with-langs.min.js'],
  less: './static/beta/less/dareyoo.less',
  less_libs: ['./static/beta/less', './static/beta/lib/bootstrap/less'],
  css_libs: [],
  fonts_libs: ['./static/beta/lib/bootstrap/dist/fonts/**']
};

gulp.task('html', function(){
  return gulp.src(paths.html)
        .pipe(size())
        //.pipe(replace('PATHX', 'foo'))
        .pipe(gulp.dest('./static/beta/build/partials'));
});

gulp.task('copy_scripts', function() {
  // Copy vendor JavaScript
  return gulp.src(paths.scripts_libs.concat(paths.scripts))
    .pipe(size())
    .pipe(gulp.dest('./static/beta/build/js'));
});

gulp.task('dareyoo_all_min_scripts', function() {
  // Unify, minify and copy all JavaScript
  return gulp.src(paths.scripts_libs.concat(paths.scripts))
    .pipe(uglify())
    //.pipe(print())
    .pipe(concat('dareyoo.all.min.js'))
    .pipe(size())
    .pipe(gulp.dest('./static/beta/build/js'));
});

// All scripts
gulp.task('scripts', ['copy_scripts', 'dareyoo_all_min_scripts']);

gulp.task('less', function () {
  return gulp.src(paths.less)
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('dareyoo.all.min.css'))
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/css'));
});

gulp.task('vendor_css', function () {
  /* return gulp.src(paths.css_libs)
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/css'));*/
});

// All css
gulp.task('css', ['less', 'vendor_css']);

gulp.task('fonts', function () {
  return gulp.src(paths.fonts_libs)
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/fonts'));
});

//Replace paths in templates/css/js depending on production/developement
gulp.task('paths', function () {
  console.log("Hola!" + args.jeje + args.jaja);
});

gulp.task('images', function () {
  console.log("Treating images...");
});

// Rerun the task when a file changes
gulp.task('watch', function() {
  gulp.watch(paths.less_libs, ['less']);
});

// Deploy to S3. TODO (this code is just an example)
gulp.task('s3', function() {
  aws = JSON.parse(fs.readFileSync('./aws.json'));
  options = { delay: 1000 } // optional delay each request by x milliseconds
  gulp.src('./dist/**', {read: false})
      .pipe(s3(aws, options));
});

gulp.task('deploy', function(done){
  //var options = {args: " -f"};
  var options = {};
  git.push('pro', 'master', options, done);
});

gulp.task('clean', function () {
    return gulp.src(['build/css', 'build/js', 'build/img', 'build/partials'], {read: false}).pipe(clean());
});

// Build
gulp.task('build', ['html', 'css', 'scripts', 'images', 'fonts']);

// Default task (called when you run `gulp` from cli)
gulp.task('default', ['clean'], function () {
    gulp.start('build');
});