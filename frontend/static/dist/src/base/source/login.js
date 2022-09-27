'use strict';

import Abc from './abc';

const e = React.createElement;

class LikeButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = { liked: false };
  }

  render() {
    if (this.state.liked) {
      return 'You liked this.';
    }

    return (
        <React.Fragment>
            <button onClick={() => this.setState({ liked: true })}>
                <Abc text="Like" />
            </button>
        </React.Fragment>
    );
  }
}

const domContainer = document.querySelector('#login');
ReactDOM.render(e(LikeButton), domContainer);