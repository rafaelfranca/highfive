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

  def fixture(name)
    File.read(File.expand_path('../fixtures/' + name, __FILE__))
  end
end
