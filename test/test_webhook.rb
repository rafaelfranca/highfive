require 'helper'

class WebhookTest < Minitest::Test
  include Rack::Test::Methods

  def app
    Webhook.new
  end

  def test_open_a_new_pull_request
    post '/', fixture('new_pr_without_assignee.json'), 'HTTP_X_GITHUB_EVENT' => 'pull_request'
    assert_equal 201, last_response.status
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
