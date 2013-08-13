(function () {

  "use strict";

  function display_error (msg) {
    if (typeof msg !== "undefined" && msg != "")
      $("#error-message").html(msg);
    else
      $("#error-message").text("Something went wrong.");
    $("#error").show();
  }

  var UglyReader = Backbone.Router.extend({
    initialize: function () {
      this.feeds_view = new FeedsView({model: new Feeds(), el: "#feeds-view"});
      this.feeds_view.model.fetch();
    },
    subscribe: function (url) {
      var this_ = this;
      $.ajax({
        url: "/api/subscribe",
        type: "POST",
        dataType: "json",
        data: {url: url},
        success: function (data) {
          this_.feeds_view.model.add(data.feed);
        },
        error: function (xhr, errorType, error) {
          display_error(eval("("+xhr.response+")").message);
        }
      });
    }
  });

  //
  // Data model and collections.
  //
  var Feed = Backbone.Model.extend({
    unsubscribe: function () {
      var this_ = this;
      $.ajax({
        url: "/api/unsubscribe/"+this_.id,
        type: "POST",
        dataType: "json",
        success: function () { this_.collection.remove(this_); },
        error: function (xhr, errorType, error) {
          display_error(eval("("+xhr.response+")").message);
        }
      });
    }
  });
  var Feeds = Backbone.Collection.extend({
    model: Feed,
    url: "/api/feeds",
    parse: function (response) { return response.feeds; },
    comparator: function (feed) { return feed.get("title"); }
  });

  //
  // Views.
  //
  var FeedsView = Backbone.View.extend({
    initialize: function() {
      this.listenTo(this.model, "add", this.render);
      this.listenTo(this.model, "remove", this.render);
    },
    template: _.template($("#feeds-template").html()),
    render: function () {
      var feeds = this.model.models;
      this.$el.html(this.template({feeds: feeds}));

      for (var i = 0, l = feeds.length; i < l; ++i) {
        var feed = new FeedView({model: feeds[i]});
        feed.render();
        this.$el.append(feed.$el);
      }

      return this;
    }
  });
  var FeedView = Backbone.View.extend({
    tagName: "div",
    className: "feed",
    events: {
      "click .unsubscribe": "unsubscribe"
    },
    unsubscribe: function () { this.model.unsubscribe(); },
    template: _.template($("#feed-template").html()),
    render: function () {
      this.$el.html(this.template(this.model.attributes));
      return this;
    }
  });

  //
  // Initialize the app.
  //
  $(function () {
    window.ugly_reader = new UglyReader();
    $(".close").on("click", function () {
      $($(this).data("dismiss")).hide();
    });
  });

})();
