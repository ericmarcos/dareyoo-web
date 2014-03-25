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

var isPro = args.pro;
var isPre = args.pre;

var paths = {
  html: ['./static/beta/partials/**'],
  scripts: ['./static/beta/js/*.js'],
  less: './static/beta/less/dareyoo.less',
  less_libs: ['./static/beta/less', './static/beta/lib/bootstrap/less']
};

gulp.task('html', function(){
  return gulp.src(paths.html)
        .pipe(size())
        //.pipe(replace('PATHX', 'foo'))
        .pipe(gulp.dest('./static/beta/build/partials'));
});

gulp.task('scripts', function() {
  // Minify and copy all JavaScript (except vendor scripts)
  return gulp.src(paths.scripts)
    .pipe(uglify())
    .pipe(concat('dareyoo.min.js'))
    .pipe(size())
    .pipe(gulp.dest('./static/beta/build/js'));
});

gulp.task('less', function () {
  return gulp.src(paths.less)
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('dareyoo.min.css'))
        .pipe(gulp.dest('./static/beta/build/css'));
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
gulp.task('build', ['html', 'less', 'scripts', 'images']);

// Default task (called when you run `gulp` from cli)
gulp.task('default', ['clean'], function () {
    gulp.start('build');
});