require 'helper'

class BotTest < Minitest::Test
  def test_handle_pull_request_do_nothing_if_reviewer_is_not_found
    client = Minitest::Mock.new
    bot = Bot.new(client)

    payload = build_payload
    payload['pull_request']['body'] = 'something'

    bot.handle_pull_request!(payload)

    client.verify
  end

  def test_handle_pull_request_assign_pr_to_reviewer_in_body
    client = Minitest::Mock.new
    bot = Bot.new(client)

    client.expect(:update_issue, true, ['rails/rails', 1234, { assignee: 'rafael_franca' }])

    payload = build_payload

    bot.handle_pull_request!(payload)

    client.verify
  end

  private

  def build_payload
    {
      'number' => 1234,
      'repository' => {
        'full_name' => 'rails/rails'
      },
      'pull_request' => {
        'body' => 'r? @rafael_franca'
      }
    }
  end
end
