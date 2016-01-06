require 'helper'

class BotTest < Minitest::Test
  def test_handle_pull_request_do_nothing_if_reviewer_is_not_found
    client = Minitest::Mock.new
    bot = Bot.new(client)

    client.expect(:contributors, [{ 'login' => 'foo' }], ['rails/rails'])

    payload = build_payload
    payload['pull_request']['body'] = 'something'

    bot.handle_pull_request!(payload)

    client.verify
  end

  def test_handle_pull_request_assign_pr_to_reviewer_in_body
    client = Minitest::Mock.new
    bot = Bot.new(client)

    client.expect(:contributors, [{ 'login' => 'foo' }], ['rails/rails'])
    client.expect(:update_issue, true, ['rails/rails', 1234, { assignee: 'rafael_franca' }])

    payload = build_payload

    bot.handle_pull_request!(payload)

    client.verify
  end

  def test_handle_pull_request_give_a_nice_comment_when_first_time_contributor
    client = Minitest::Mock.new
    bot = Bot.new(client)

    message = <<~MSG
    Thanks for the pull request, and welcome! The Rails team is excited to review your changes, and you should hear from @rafael_franca (or someone else) soon.

    If any changes to this PR are deemed necessary, please add them as extra commits. This ensures that the reviewer can see what has changed since they last reviewed the code. Due to the way GitHub handles out-of-date commits, this should also make it reasonably obvious what issues have or haven't been addressed. Large or tricky changes may require several passes of review and changes.

    Please see [the contribution instructions](http://edgeguides.rubyonrails.org/contributing_to_ruby_on_rails.html) for more information.
    MSG

    client.expect(:contributors, [], ['rails/rails'])
    client.expect(:update_issue, true, ['rails/rails', 1234, { assignee: 'rafael_franca' }])
    client.expect(:add_comment, true, ['rails/rails', 1234, message])

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
        'body' => 'r? @rafael_franca',
        'user' => {
          'login' => 'foo'
        }
      }
    }
  end
end
