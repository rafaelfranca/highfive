require 'helper'

class BotTest < Minitest::Test
  def test_handle_pull_request
    assert_nil Bot.new.handle_pull_request!({})
  end
end
