require 'helper'

class WebhookTest < Minitest::Test
  include Rack::Test::Methods

  def setup
    super
    @bot = Minitest::Mock.new
  end

  def app
    Webhook.new(@bot)
  end

  def test_open_a_new_pull_request
    @bot.expect(:handle_pull_request!, true, [Hash])
    post '/', fixture('new_pr_without_assignee.json'), 'HTTP_X_GITHUB_EVENT' => 'pull_request'
    assert_equal 201, last_response.status
    @bot.verify
  end

  def test_any_action_in_a_pull_request
    post '/', fixture('close_pr.json'), 'HTTP_X_GITHUB_EVENT' => 'pull_request'
    assert_equal 200, last_response.status
  end

  def test_any_event
    post '/', "", 'HTTP_X_GITHUB_EVENT' => 'fork'
    assert_equal 200, last_response.status
  end

  def fixture(name)
    File.read(File.expand_path('../fixtures/' + name, __FILE__))
  end
end
